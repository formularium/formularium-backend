import datetime
import uuid

from django.conf import settings
from django.core.exceptions import PermissionDenied
from oauthlib.common import to_unicode, Request, log
from oauthlib.oauth2.rfc6749 import utils

from oauthlib.oauth2 import Server as OAuth2Server, RequestValidator, TokenEndpoint, BearerToken
from oauthlib.oauth2.rfc6749 import catch_errors_and_unavailability
from rest_framework_social_oauth2.oauth2_grants import SocialTokenGrant


def generate_signed_token(private_pem, request):
    """generate, enriches and signs the jwt tokens
        :param private_pem: the private key that should be used to sign the token
        :param request: the request object the jwt token should be signed for
    """
    import jwt

    # check again if the client is usable (this time we are sure there is a user object)
    if not request.client.is_usable(request):
        raise PermissionDenied

    now = datetime.datetime.utcnow()

    claims = {
        'scopes': request.scopes,
        'client': request.client.client_id,
        # support implicit grants
        'user': request.user.pk if request.user else request.client.user.pk,
        'groups': [group.name for group in request.user.groups.all()] if request.user else
            [group.name for group in request.client.user.groups.all()],
        'token_id': str(uuid.uuid4()),
        'exp': now + datetime.timedelta(seconds=request.expires_in)
    }



    claims.update(request.claims)

    token = jwt.encode(claims, private_pem, 'RS256')
    token = to_unicode(token, "UTF-8")
    return token


def signed_token_generator(private_pem, **kwargs):
    """ generator for signed token generators
    :param private_pem:
    """
    def signed_token_generator(request):
        request.claims = kwargs

        return generate_signed_token(private_pem, request)

    return signed_token_generator


class Oauth2JWTTokenServer(OAuth2Server):
    """This Oauth2 server injects the jwt token generator into the server itself"""

    def __init__(self, request_validator, token_expires_in=None,
                 token_generator=None, refresh_token_generator=None,
                 *args, **kwargs):
        jwt_private_rsa = getattr(settings, "JWT_PRIVATE_KEY_RSA", None)
        jwt_issuer = getattr(settings, "JWT_ISSUER", None)

        if getattr(settings, "JWT_ENABLED", False):
            token_generator = signed_token_generator(jwt_private_rsa, issuer=jwt_issuer)
        super().__init__(request_validator,
                         token_expires_in=token_expires_in,
                         token_generator=token_generator,
                         refresh_token_generator=refresh_token_generator)


class Oauth2JWTSocialTokenServer(TokenEndpoint):

    """An endpoint used only for token generation."""

    def __init__(self, request_validator, token_generator=None,
                 token_expires_in=None, refresh_token_generator=None, **kwargs):
        """Construct a client credentials grant server.
        :param request_validator: An implementation of
                                  oauthlib.oauth2.RequestValidator.
        :param token_expires_in: An int or a function to generate a token
                                 expiration offset (in seconds) given a
                                 oauthlib.common.Request object.
        :param token_generator: A function to generate a token from a request.
        :param refresh_token_generator: A function to generate a token from a
                                        request for the refresh token.
        :param kwargs: Extra parameters to pass to authorization-,
                       token-, resource-, and revocation-endpoint constructors.
        """
        jwt_private_rsa = getattr(settings, "JWT_PRIVATE_KEY_RSA", None)
        jwt_issuer = getattr(settings, "JWT_ISSUER", None)
        if getattr(settings, "JWT_ENABLED", False):
            token_generator = signed_token_generator(jwt_private_rsa, issuer=jwt_issuer)

        refresh_grant = SocialTokenGrant(request_validator)
        bearer = BearerToken(request_validator, token_generator,
                             token_expires_in, refresh_token_generator)

        TokenEndpoint.__init__(self, default_grant_type='convert_token',
                               grant_types={
                                   'convert_token': refresh_grant,
                               },
                               default_token_type=bearer)

    # We override this method just so we can pass the django request object
    @catch_errors_and_unavailability
    def create_token_response(self, uri, http_method='GET', body=None,
                              headers=None, credentials=None, grant_type_for_scope=None,
                              claims=None):
        """Extract grant_type and route to the designated handler."""
        django_request = headers.pop("Django-request-object", None)
        request = Request(
            uri, http_method=http_method, body=body, headers=headers)

        # 'scope' is an allowed Token Request param in both the "Resource Owner Password Credentials Grant"
        # and "Client Credentials Grant" flows
        # https://tools.ietf.org/html/rfc6749#section-4.3.2
        # https://tools.ietf.org/html/rfc6749#section-4.4.2
        request.scopes = utils.scope_to_list(request.scope)

        # OpenID Connect claims, if provided.  The server using oauthlib might choose
        # to implement the claims parameter of the Authorization Request.  In this case
        # it should retrieve those claims and pass them via the claims argument here,
        # as a dict.
        if claims:
            request.claims = claims

        if grant_type_for_scope:
            request.grant_type = grant_type_for_scope

        request.extra_credentials = credentials
        request.django_request = django_request
        grant_type_handler = self.grant_types.get(request.grant_type,
                                                  self.default_grant_type_handler)
        log.debug('Dispatching grant_type %s request to %r.',
                  request.grant_type, grant_type_handler)
        return grant_type_handler.create_token_response(
            request, self.default_token_type)


