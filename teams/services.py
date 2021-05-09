import josepy
import json
import requests
from acme import challenges
from acme.client import ClientV2, ClientNetwork
from acme.messages import Directory, Registration
from certbot._internal.client import acme_from_config_key
from cryptography.hazmat.backends import default_backend
from django.contrib.auth.models import AbstractUser
from josepy import JWKRSA
from letsencrypt.models import AcmeChallenge
from serious_django_services import Service, CRUDMixin, NotPassed
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from django.conf import settings

from forms.services.forms import FormServiceException
from teams.forms import (
    CreateTeamForm,
    UpdateTeamForm,
    CreateTeamMembershipForm,
    UpdateTeamMembershipForm,
)
from teams.models import (
    Team,
    TeamRoleChoices,
    TeamMembership,
    TeamStatus,
    TeamCertificate,
    EncryptionKey,
)
from teams.permissions import (
    CanCreateTeamPermission,
    CanRemoveTeamMemberPermission,
    CanActivateEncryptionKeyPermission,
    CanAddEncryptionKeyPermission,
)


class TeamServiceException(Exception):
    pass


class TeamService(Service, CRUDMixin):
    service_exceptions = (TeamServiceException,)

    update_form = UpdateTeamForm
    create_form = CreateTeamForm

    model = Team

    @classmethod
    def create(cls, user: AbstractUser, name: str, key: str) -> Team:
        """
        creates a new user and makes them admin
        :param csr: the certificate request
        :param public_key: public key for this team
        :param user: user calling the service (needs CanCreateTeamPermission permission)
        :param name: name of the Team
        :param key: the newly generated public key
        :return: the newly generated team
        """
        if not user.has_perm(CanCreateTeamPermission):
            raise TeamServiceException(
                "You don't have the permission to create a new team"
            )

        team = cls._create({"name": name})

        TeamMembershipService.add_member(
            user=user,
            team_id=team.id,
            key=key,
            invited_user_id=user.id,
            role=TeamRoleChoices.ADMIN,
        )
        return team

    @classmethod
    def add_csr(cls, user, team_id: int, csr: str, public_key: str):
        """
        add the signed certificate to the team
        :param user: user calling the service
        :param team_id: id of the team
        :param csr: the certificate request
        :param public_key: the public_key
        :return: team object
        """
        if not user.has_perm(CanCreateTeamPermission):
            raise TeamServiceException(
                "You don't have the permission to create a new team"
            )

        team = cls.retrieve(user, team_id)
        TeamCertificateService.create_certificate(team, csr, public_key, user.email)

        return team

    @classmethod
    def retrieve(cls, user, id: int) -> Team:
        """
        retrieve a team object
        :param user: user calling the service
        :param id: id of the team
        :return: team object
        """
        return cls._retrieve(id)


class TeamMembershipService(Service, CRUDMixin):
    service_exceptions = (TeamServiceException,)

    update_form = UpdateTeamMembershipForm
    create_form = CreateTeamMembershipForm

    model = TeamMembership

    @classmethod
    def add_member(
        cls,
        user: AbstractUser,
        team_id: int,
        key: str,
        invited_user_id: int,
        role: TeamRoleChoices = TeamRoleChoices.MEMBER,
    ) -> TeamMembership:
        """
        creates a new user and makes them admin
        :param invited_user_id: the user that sould be added
        :param role: the role the newly created Member should have (Admin or Member)
        :param team_id: the id of the team the user should be added to
        :param user: user calling the services (needs CanCreateTeamPermission permission)
        :param key: the newly generated public key
        :return: the newly generated team
        """

        team = TeamService.retrieve(user, team_id)

        if (
            not (
                user.has_perm(CanCreateTeamPermission)
                and team.members.count() == 0
                and invited_user_id == user.pk
            )
            and not team.members.filter(user=user, role=TeamRoleChoices.ADMIN).exists()
        ):
            raise TeamServiceException(
                "You don't have the permission to create a new team"
            )

        team_membership = cls._create(
            {
                "team": team_id,
                "key": key,
                "user": invited_user_id,
                "role": role,
            }
        )

        return team_membership

    @classmethod
    def update_member(
        cls,
        user: AbstractUser,
        team_id: int,
        affected_user_id: int,
        key: str = NotPassed,
        role: TeamRoleChoices = NotPassed,
    ) -> TeamMembership:
        """
        update a team member
        :param user: the user calling the serviceis affected
        :param key: the new encrypted key for this user
        :param affected_user_id: the user that affects this change
        :param role: role of the user
        :return: team membership object
        """
        team = TeamService.retrieve(user, team_id)

        if not team.members.filter(user=user, role=TeamRoleChoices.ADMIN).exists():
            raise TeamServiceException(
                "You don't have the permission to edit a team member."
            )

        if not team.members.filter(user=affected_user_id).exists():
            raise TeamServiceException(
                "This user is not in the team you want to change."
            )

        membership = team.members.filter(user=affected_user_id).get()

        if (
            role == TeamRoleChoices.MEMBER
            and membership.role == TeamRoleChoices.ADMIN
            and team.members.filter(role=TeamRoleChoices.ADMIN).count() == 1
        ):
            raise TeamServiceException(
                "This user can't become a member because every team needs at least one admin."
            )

        cls._update(
            membership.id,
            {
                "key": key,
                "role": role,
            },
        )
        membership.refresh_from_db()
        return membership

    @classmethod
    def remove_member(
        cls, user: AbstractUser, team_id: int, affected_user_id: int
    ) -> bool:
        """
        update a team member
        :param user: user calling the service
        :param team_id: id of the team the user should be removed from
        :param affected_user_id: the user that should be removed
        :return: True if user has been sucessfully removed
        """

        team = TeamService.retrieve(user, team_id)

        if not team.members.filter(
            user=user, role=TeamRoleChoices.ADMIN
        ).exists() and not user.has_perm(CanRemoveTeamMemberPermission):
            raise TeamServiceException(
                "You don't have the permission to remove a team member."
                "You must be either team admin or have the permission 'CanRemoveTeamMemberPermission'."
            )

        membership = team.members.filter(user=affected_user_id).get()

        if (
            team.members.filter(role=TeamRoleChoices.ADMIN).count() == 1
            and membership.role == TeamRoleChoices.ADMIN
        ):
            raise TeamServiceException(
                "This user can't be removed because every team needs at least one admin."
            )

        return cls._delete(membership.id)


class TeamCertificateService(Service):
    service_exceptions = (TeamServiceException,)

    @classmethod
    def create_certificate(
        cls, team: Team, csr: str, public_key: str, contact_email: str
    ):
        """
        generate a new certificate for a team based on a csr
        :param team: the teamobject the certificate should be generated for
        :param csr: the csr request
        :param public_key: the public key for the csr
        :param contact_email: the contact email mentioned in the csr
        :return: the certificate object
        """
        cert = TeamCertificate.objects.create(team=team, public_key=public_key, csr=csr)
        if settings.TESTING:
            cert.status = TeamStatus.ACTIVE
            cert.save()
            return cert.public_key
        acme = ACMEService.register_account(contact_email)
        challenge, validation = acme.new_order(csr)
        challenge = AcmeChallenge.objects.create(
            challenge=challenge, response=validation
        )
        pem = acme.retrieve_certificate()
        cert.certificate = pem
        cert.status = TeamStatus.ACTIVE
        cert.save()
        return cert


# inspired by https://github.com/certbot/certbot/blob/2622a700e0a83e0de0994c970929b624b98dad40/acme/examples/http01_example.py#L67
class ACMEService(Service):
    service_exceptions = (TeamServiceException,)

    def __init__(self, client):
        self.client = client

    def new_order(self, csr: str):
        """
        create a new acme order
        :param csr: the csr
        :return: returs the challenge, the response
        """
        self.order = self.client.new_order(csr)
        self.challenge = self.select_http01_challenge()
        self.response, validation = self.challenge.response_and_validation(
            self.client.net.key
        )

        return self.challenge.path.split("/")[-1], validation

    def retrieve_certificate(self):
        """retrieve the certificate after we provided the challenge response"""
        self.client.answer_challenge(self.challenge, self.response)

        # Wait for challenge status and then issue a certificate.
        # It is possible to set a deadline time.
        finalized_order = self.client.poll_and_finalize(self.order)

        return finalized_order.fullchain_pem

    @classmethod
    def _get_directory(cls, directory_url):
        """fetches the directory information
        :return: the Directory` object
        """
        directory = requests.get(directory_url)
        return Directory(directory.json())

    @classmethod
    def _generate_keypair(cls):
        """
        generate the jwk keypair for the key request
        :return: the JWKRSA object
        """
        rsa_key = generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
        return josepy.JWKRSA(key=josepy.ComparableRSAKey(rsa_key))

    @classmethod
    def register_account(
        cls,
        email: str,
        directory_url: str = "https://acme-v02.api.letsencrypt.org/directory",
    ):
        """
        create a new acme account
        :param email: the email address that should be used for the account
        :param directory_url: the url of the acme directory that should be used
        :return: a new ACME client instance
        """
        keypair = cls._generate_keypair()
        client_network = ClientNetwork(keypair)
        directory = cls._get_directory(directory_url)
        registration = Registration.from_data(email=email, terms_of_service_agreed=True)
        client = ClientV2(directory, client_network)
        result = client.new_account(registration)
        return ACMEService(client)

    def select_http01_challenge(self):
        """Extract authorization resource from within order resource."""
        # Authorization Resource: authz.
        # This object holds the offered challenges by the server and their status.
        authz_list = self.order.authorizations

        for authz in authz_list:
            # Choosing challenge.
            # authz.body.challenges is a set of ChallengeBody objects.
            for i in authz.body.challenges:
                # Find the supported challenge.
                if isinstance(i.chall, challenges.HTTP01):
                    return i

        raise Exception("HTTP-01 challenge was not offered by the CA server.")


class EncryptionKeyService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def add_key(cls, user: AbstractUser, public_key: str) -> EncryptionKey:
        """
        submit a generated key for a user
        :param user: the user calling the service
        :param public_key: their public key
        :return: id/information about key creation
        """
        if not user.has_perm(CanAddEncryptionKeyPermission):
            raise PermissionError("You are not allowed to add a form key")
        return EncryptionKey.objects.create(
            user=user, public_key=public_key, active=False
        )

    @classmethod
    def activate_key(cls, user: AbstractUser, public_key_id: int) -> EncryptionKey:
        """
        activate a submitted public key that is used to share form keys between users
        :param user: the user calling the service
        :param public_key_id: id the of the public key that should be activated
        :return: the activated key object
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to activate this form key")
        public_key = EncryptionKey.objects.get(id=public_key_id)

        if public_key.active == True:
            raise FormServiceException("This public key is already active.")

        public_key.active = True
        public_key.save()

        return public_key

    @classmethod
    def remove_key(cls, user: AbstractUser, public_key_id: int) -> bool:
        """
        remove a submitted public key that is used to share form keys between users
        :param user: the user calling the service
        :param public_key_id: id the of the public key that should be activated
        :return: the activated key object
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to activate this form key")
        public_key = EncryptionKey.objects.get(id=public_key_id)

        public_key.delete()

        return True
