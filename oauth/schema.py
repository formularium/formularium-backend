from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as DjGroup

import graphene
from django_graphene_permissions import permissions_checker
from django_graphene_permissions.permissions import IsAuthenticated
from graphene import relay, ObjectType, Field
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from serious_django_graphene import (
    get_user_from_info,
    FailableMutation,
    MutationExecutionException,
)

from oauth.services import UserProfileService


class Group(DjangoObjectType):
    """Group Node"""

    class Meta:
        model = DjGroup
        filter_fields = {}


class UserType(DjangoObjectType):
    """
    User Node
    """

    language = graphene.String()
    profile_picture = graphene.String()
    name_on_po_box = graphene.String()
    profile_setup_done = graphene.Boolean()
    newsletter = graphene.Boolean()

    def resolve_language(self, info):
        return self.profile.language

    def resolve_profile_picture(self, info):
        if self.profile.profile_picture:
            return self.profile.profile_picture.url

    def resolve_profile_setup_done(self, info):
        return self.profile.profile_setup_done

    class Meta:
        model = get_user_model()
        filter_fields = {}
        exclude_fields = (
            "password",
            "is_superuser",
            "is_staff",
            "last_login",
            "date_joined",
            "is_active",
            "username",
        )

    @classmethod
    @permissions_checker([IsAuthenticated])
    def get_node(cls, info, id):
        try:
            item = cls._meta.model.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class LanguageType(ObjectType):
    """Language object"""

    language = graphene.String()
    iso_code = graphene.String()


class UserQuery(object):
    """
    what is an abstract type?
    http://docs.graphene-python.org/en/latest/types/abstracttypes/
    """

    user = relay.Node.Field(UserType)


class Query(ObjectType):

    me = graphene.Field(UserType)
    get_available_languages = graphene.List(LanguageType)

    def resolve_me(self, info, **kwargs):
        user = get_user_from_info(info)
        if user.is_authenticated:
            return get_user_from_info(info)
        return None

    def resolve_get_available_languages(self, info, **kwargs):
        user = get_user_from_info(info)
        return UserProfileService.get_available_language(user)


class UpdateMyUserProfile(FailableMutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        language = graphene.String()

    me = graphene.Field(UserType)

    @permissions_checker([IsAuthenticated])
    def mutate(self, info, **kwargs):
        user = get_user_from_info(info)

        try:
            user = UserProfileService.update_user_basic_information(user=user, **kwargs)
        except UserProfileService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateMyUserProfile(me=user, success=True)


class UploadProfilePicture(FailableMutation):
    class Arguments:
        profile_picture = Upload(required=True)

    me = graphene.Field(UserType)

    @permissions_checker([IsAuthenticated])
    def mutate(self, info, **kwargs):
        user = get_user_from_info(info)
        file_ = kwargs["profile_picture"]

        try:
            user = UserProfileService.upload_profile_picture(user=user, picture=file_)
        except UserProfileService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UploadProfilePicture(me=user, success=True)


class Mutation(graphene.ObjectType):
    update_my_user_profile = UpdateMyUserProfile.Field()
    upload_my_profile_picture = UploadProfilePicture.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
