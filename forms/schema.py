import graphene
from django_graphene_permissions import PermissionDjangoObjectType, permissions_checker
from django_graphene_permissions.permissions import IsAuthenticated
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_permissions.mixins import AuthNode
from serious_django_graphene import (
    get_user_from_info,
    FailableMutation,
    MutationExecutionException,
)
from graphql_relay.node.node import from_global_id

from serious_django_graphene import (
    get_user_from_info,
    FormMutation,
    MutationExecutionException,
)
from graphql_relay.node.node import from_global_id
from graphene_django.filter import DjangoFilterConnectionField
from graphene.utils.str_converters import to_snake_case

## Queries
from serious_django_services import NotPassed

from forms.models import (
    Form,
    EncryptionKey,
    FormSubmission,
    FormSchema,
    FormTranslation,
    TranslationKey,
    Team,
    TeamMembership,
    TeamRoleChoices,
)
from forms.permissions import (
    CanRetrieveFormSubmissionsPermission,
    CanAddEncryptionKeyPermission,
    CanEditFormPermission,
    CanAddFormTranslationPermission,
    CanActivateEncryptionKeyPermission,
)
from forms.services.forms import (
    FormService,
    FormServiceException,
    FormReceiverService,
    EncryptionKeyService,
    FormSchemaService,
    FormTranslationService,
)
from graphene_permissions.permissions import AllowAuthenticated

from forms.services.teams import TeamService, TeamMembershipService


class FormNode(DjangoObjectType):
    class Meta:
        model = Form
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


class InternalFormNode(DjangoObjectType):
    class Meta:
        model = Form
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def get_node(cls, info, id):
        try:
            item = Form.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class InternalTeamNode(DjangoObjectType):
    class Meta:
        model = Team
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated])
    def get_node(cls, info, id):
        try:
            item = Team.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class InternalTeamMembershipNode(DjangoObjectType):
    class Meta:
        model = TeamMembership
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated])
    def get_node(cls, info, id):
        try:
            item = TeamMembership.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class FormSchemaNode(DjangoObjectType):
    class Meta:
        model = FormSchema
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(form__active=True)


class FormTranslationNode(DjangoObjectType):
    class Meta:
        model = FormTranslation
        filter_fields = ["id", "language"]
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True, form__active=True)


class TranslationKeyNode(DjangoObjectType):
    class Meta:
        model = TranslationKey
        filter_fields = ["id"]
        interfaces = (relay.Node,)


class InternalFormSchemaNode(DjangoObjectType):
    class Meta:
        model = FormSchema
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def get_node(cls, info, id):
        try:
            item = FormSchema.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class FormSubmissionNode(PermissionDjangoObjectType):
    class Meta:
        model = FormSubmission
        filter_fields = ["id"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated, CanRetrieveFormSubmissionsPermission])
    def get_node(cls, info, id):
        user = get_user_from_info(info)

        try:
            item = (
                FormReceiverService.retrieve_submitted_forms(user).filter(id=id).get()
            )
        except cls._meta.model.DoesNotExist:
            return None
        return item


class InternalFormTranslationNode(PermissionDjangoObjectType):
    class Meta:
        model = FormTranslation
        filter_fields = ["id", "language"]
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def get_node(cls, info, id):
        try:
            item = FormTranslation.objects.filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class EncryptionKeyNode(DjangoObjectType):
    fingerprint = graphene.Field(graphene.String)

    class Meta:
        model = EncryptionKey

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


class InactiveEncryptionKeyNode(PermissionDjangoObjectType):
    fingerprint = graphene.Field(graphene.String)

    class Meta:
        model = EncryptionKey
        filter_fields = ["id"]
        interfaces = (relay.Node,)


class Query(graphene.ObjectType):
    # get a single form
    form = relay.Node.Field(FormNode)
    # get a single form submission
    form_submission = relay.Node.Field(FormSubmissionNode)
    # get a list of available forms
    all_forms = DjangoFilterConnectionField(FormNode)
    # get a list of available form submissions
    all_form_submissions = DjangoFilterConnectionField(FormSubmissionNode)

    # get a list of available teams
    all_teams = DjangoFilterConnectionField(InternalTeamNode)
    # get a list of available teams
    team = relay.Node.Field(InternalTeamNode)
    # get public keys for form
    public_keys_for_form = graphene.List(
        EncryptionKeyNode, form_id=graphene.ID(required=True)
    )

    # get all forms - also inactive, for the admin interface
    internal_form = relay.Node.Field(InternalFormNode)
    all_inactive_encryption_keys = DjangoFilterConnectionField(
        InactiveEncryptionKeyNode
    )
    all_internal_forms = DjangoFilterConnectionField(InternalFormNode)

    form_schema = relay.Node.Field(FormSchemaNode)
    internal_form_schema = relay.Node.Field(InternalFormSchemaNode)

    def resolve_public_keys_for_form(self, info, form_id):
        return FormService.retrieve_public_keys_for_form(
            int(from_global_id(form_id)[1])
        )

    @permissions_checker([IsAuthenticated, CanRetrieveFormSubmissionsPermission])
    def resolve_all_form_submissions(self, info, **kwargs):
        user = get_user_from_info(info)
        return FormReceiverService.retrieve_submitted_forms(user)

    @permissions_checker([IsAuthenticated, CanActivateEncryptionKeyPermission])
    def resolve_all_inactive_encryption_keys(self, info, **kwargs):
        user = get_user_from_info(info)
        return EncryptionKey.objects.filter(active=False)

    @permissions_checker([IsAuthenticated])
    def resolve_all_teams_(self, info, **kwargs):
        user = get_user_from_info(info)
        return Team.objects.all()

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def resolve_all_internal_forms(self, info, **kwargs):
        user = get_user_from_info(info)
        return Form.objects.all()


class SubmitForm(FailableMutation):
    content = graphene.String()
    signature = graphene.String()

    class Arguments:
        form_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    def mutate(self, info, form_id, content):
        try:
            result = FormService.submit(int(from_global_id(form_id)[1]), content)
        except FormService.exceptions as e:
            raise MutationExecutionException(str(e))
        return SubmitForm(success=True, **result)


class SubmitEncryptionKey(FailableMutation):
    encryption_key = graphene.Field(EncryptionKeyNode)

    class Arguments:
        public_key = graphene.String(required=True)

    @permissions_checker([IsAuthenticated, CanAddEncryptionKeyPermission])
    def mutate(self, info, public_key):
        user = get_user_from_info(info)
        try:
            result = EncryptionKeyService.add_key(user, public_key)
        except EncryptionKeyService.exceptions as e:
            raise MutationExecutionException(str(e))
        return SubmitEncryptionKey(success=True, encryption_key=result)


class ActivateEncryptionKey(FailableMutation):
    encryption_key = graphene.Field(EncryptionKeyNode)

    class Arguments:
        public_key_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanActivateEncryptionKeyPermission])
    def mutate(self, info, public_key_id):
        user = get_user_from_info(info)
        try:
            result = EncryptionKeyService.activate_key(
                user, int(from_global_id(public_key_id[0]))
            )
        except EncryptionKeyService.exceptions as e:
            raise MutationExecutionException(str(e))
        return ActivateEncryptionKey(success=True, encryption_key=result)


class CreateForm(FailableMutation):
    form = graphene.Field(InternalFormNode)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, name, description):
        user = get_user_from_info(info)
        try:
            result = FormService.create_form_(user, name, description)
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateForm(success=True, form=result)


class CreateFormSchema(FailableMutation):
    form_schema = graphene.Field(FormSchemaNode)

    class Arguments:
        schema = graphene.String(required=True)
        key = graphene.String(required=True)
        form_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, schema, key, form_id):
        user = get_user_from_info(info)
        try:
            result = FormSchemaService.create_form_schema(
                user, key, int(from_global_id(form_id)[1]), schema
            )
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateFormSchema(success=True, form_schema=result)


class CreateFormTranslation(FailableMutation):
    form_translation = graphene.Field(InternalFormTranslationNode)

    class Arguments:
        language = graphene.String(required=True)
        region = graphene.String(required=True)
        form_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, form_id, language, region):
        user = get_user_from_info(info)
        try:
            result = FormTranslationService.create_form_translation(
                user,
                form_id=int(from_global_id(form_id)[1]),
                language=language,
                region=region,
            )
        except FormTranslationService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateFormTranslation(success=True, form_translation=result)


class CreateTeam(FailableMutation):
    team = graphene.Field(InternalTeamNode)

    class Arguments:
        name = graphene.String(required=True)
        public_key = graphene.String(required=True)
        key = graphene.String(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, name, public_key, key):
        user = get_user_from_info(info)
        try:
            result = TeamService.create(user, name=name, public_key=public_key, key=key)
        except TeamService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateTeam(success=True, team=result)


TeamRoleChoicesSchema = graphene.Enum.from_enum(TeamRoleChoices)


class AddTeamMember(FailableMutation):
    membership = graphene.Field(InternalTeamMembershipNode)

    class Arguments:
        key = graphene.ID(required=True)
        team_id = graphene.ID(required=True)
        invited_user_id = graphene.ID(required=True)
        role = TeamRoleChoicesSchema()

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, key, team_id, invited_user_id, role):
        user = get_user_from_info(info)
        try:
            result = TeamMembershipService.add_member(
                user,
                key=key,
                team_id=int(from_global_id(team_id)[1]),
                invited_user_id=int(from_global_id(invited_user_id)[1]),
                role=role,
            )
        except TeamMembershipService.exceptions as e:
            raise MutationExecutionException(str(e))
        return AddTeamMember(success=True, membership=result)


class UpdateTeamMember(FailableMutation):
    membership = graphene.Field(InternalTeamMembershipNode)

    class Arguments:
        key = graphene.ID(required=True)
        team_id = graphene.ID(required=True)
        affected_user_id = graphene.ID(required=True)
        role = TeamRoleChoicesSchema()

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, key, team_id, affected_user_id, role):
        user = get_user_from_info(info)
        try:
            result = TeamMembershipService.update_member(
                user,
                key=key,
                team_id=int(from_global_id(team_id)[1]),
                affected_user_id=int(from_global_id(affected_user_id)[1]),
                role=role,
            )
        except TeamMembershipService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateTeamMember(success=True, membership=result)


class RemoveTeamMember(FailableMutation):
    class Arguments:
        team_id = graphene.ID(required=True)
        affected_user_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, team_id, affected_user_id):
        user = get_user_from_info(info)
        try:
            result = TeamMembershipService.remove_member(
                user,
                team_id=int(from_global_id(team_id)[1]),
                affected_user_id=int(from_global_id(affected_user_id)[1]),
            )
        except TeamMembershipService.exceptions as e:
            raise MutationExecutionException(str(e))
        return RemoveTeamMember(success=True)


class CreateOrUpdateFormSchema(FailableMutation):
    form_schema = graphene.Field(FormSchemaNode)

    class Arguments:
        schema = graphene.String(required=True)
        key = graphene.String(required=True)
        form_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, schema, key, form_id):
        user = get_user_from_info(info)
        try:
            result = FormSchemaService.create_or_update_form_schema(
                user, key, int(from_global_id(form_id)[1]), schema
            )
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateOrUpdateFormSchema(success=True, form_schema=result)


class UpdateFormSchema(FailableMutation):
    form_schema = graphene.Field(FormSchemaNode)

    class Arguments:
        schema_id = graphene.ID(required=True)
        schema = graphene.String(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, schema_id, schema):
        user = get_user_from_info(info)
        try:
            result = FormSchemaService.update_form_schema(user, schema_id, schema)
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateFormSchema(success=True, form_schema=result)


class UpdateFormTranslationKey(FailableMutation):
    translation_key = graphene.Field(TranslationKeyNode)

    class Arguments:
        key = graphene.String(required=True)
        value = graphene.String(required=True)
        translation_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, translation_id, key, value):
        user = get_user_from_info(info)
        try:
            result = FormTranslationService.update_translation_string(
                user,
                translation_id=int(from_global_id(translation_id)[1]),
                key=key,
                value=value,
            )
        except FormTranslationService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateFormTranslationKey(success=True, translation_key=result)


class UpdateFormTranslation(FailableMutation):
    form_translation = graphene.Field(InternalFormTranslationNode)

    class Arguments:
        language = graphene.String(required=True)
        region = graphene.String(required=True)
        translation_id = graphene.ID(required=True)
        active = graphene.Boolean(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, translation_id, language, region, active):
        user = get_user_from_info(info)
        try:
            result = FormTranslationService.update_form_translation(
                user,
                translation_id=int(from_global_id(translation_id)[1]),
                language=language,
                region=region,
                active=active,
            )
        except FormTranslationService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateFormTranslation(success=True, form_translation=result)


class UpdateForm(FailableMutation):
    form = graphene.Field(InternalFormNode)

    class Arguments:
        form_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        xml_code = graphene.String()
        js_code = graphene.String()
        active = graphene.Boolean()

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(
        self,
        info,
        form_id,
        name=NotPassed,
        description=NotPassed,
        xml_code=NotPassed,
        js_code=NotPassed,
        active=NotPassed,
    ):
        user = get_user_from_info(info)
        try:
            result = FormService.update_form_(
                user,
                int(from_global_id(form_id)[1]),
                name=name,
                description=description,
                xml_code=xml_code,
                js_code=js_code,
                active=active,
            )
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return UpdateForm(success=True, form=result)


class Mutation(graphene.ObjectType):
    submit_form = SubmitForm.Field()
    submit_encryption_key = SubmitEncryptionKey.Field()
    activate_encryption_key = ActivateEncryptionKey.Field()
    create_form_schema = CreateFormSchema.Field()
    update_form_schema = UpdateFormSchema.Field()
    create_form = CreateForm.Field()
    update_form = UpdateForm.Field()
    create_form_translation = CreateFormTranslation.Field()
    update_form_translation = UpdateFormTranslation.Field()
    update_form_translation_key = UpdateFormTranslationKey.Field()
    create_or_update_schema = CreateOrUpdateFormSchema.Field()

    create_team = CreateTeam.Field()
    add_team_member = AddTeamMember.Field()
    update_team_member = UpdateTeamMember.Field()
    remove_team_member = RemoveTeamMember.Field()


## Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
