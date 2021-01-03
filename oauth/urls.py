from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt

from graphene_file_upload.django import FileUploadGraphQLView

import json


from oauth2_provider import urls as oauth2_provider_urls
from oauth2_provider_jwt.views import TokenView, JWTAuthorizationView
from oauth2_provider import views


urlpatterns = [
    path(r"authorize/", JWTAuthorizationView.as_view(), name="authorize"),
    path(r"token/", TokenView.as_view(), name="token"),
    path(r"revoke_token/", views.RevokeTokenView.as_view(),
        name="revoke-token"),
    path(r"introspect/", views.IntrospectTokenView.as_view(),
        name="introspect"),
]

urlpatterns += oauth2_provider_urls.management_urlpatterns
urlpatterns += oauth2_provider_urls.oidc_urlpatterns
