import ast
import json
import logging
from oauth2_provider_jwt.utils import generate_payload, encode_jwt
from oauth2_provider_jwt.views import MissingIdAttribute, logger

from urllib.parse import urlencode, urlparse, parse_qs  # noqa

from django.conf import settings
from django.utils.module_loading import import_string
from oauth2_provider import views
from oauth2_provider.http import OAuth2ResponseRedirect
from oauth2_provider.models import get_access_token_model
