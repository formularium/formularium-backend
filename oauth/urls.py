from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt

from graphene_file_upload.django import FileUploadGraphQLView

import json


from oauth2_provider import urls as oauth2_provider_urls
from oauth2_provider_jwt import urls as oauth2_provider_jwt_urls

urlpatterns = [
]

urlpatterns += oauth2_provider_urls.management_urlpatterns
urlpatterns += oauth2_provider_urls.oidc_urlpatterns
urlpatterns += oauth2_provider_jwt_urls.urlpatterns
