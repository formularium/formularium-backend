"""settings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt

from graphene_file_upload.django import FileUploadGraphQLView

import json
from rest_framework.exceptions import NotAuthenticated

from forms.views import pgp_signature_key, home

from oauth2_provider import urls as oauth2_provider_urls


class PrivateGraphQLView(LoginRequiredMixin, FileUploadGraphQLView):
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        data = {"status": "unauthorized"}
        try:
            if not request.user.is_authenticated:
                return HttpResponse(json.dumps(data), content_type="application/json")
        except Exception as e:
            return NotAuthenticated()

        return super(PrivateGraphQLView, self).dispatch(request, *args, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),
    path("pgp-signature-key.txt", pgp_signature_key),
    path(r"oauth/", include(("oauth.urls", "oauth"), namespace="oauth2_provider")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", home),
]
