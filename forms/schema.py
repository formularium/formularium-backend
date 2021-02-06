import graphene
from django_graphene_permissions import PermissionDjangoObjectType, permissions_checker
from django_graphene_permissions.permissions import IsAuthenticated
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_permissions.mixins import AuthNode
from serious_django_graphene import get_user_from_info, FailableMutation, MutationExecutionException
from graphql_relay.node.node import from_global_id

from serious_django_graphene import get_user_from_info, \
    FormMutation, MutationExecutionException
from graphql_relay.node.node import from_global_id
from graphene_django.filter import DjangoFilterConnectionField
from graphene.utils.str_converters import to_snake_case

## Queries
from forms.models import Form, EncryptionKey, FormSubmission, FormSchema
from forms.permissions import CanRetrieveFormSubmissionsPermission, CanAddEncryptionKeyPermission, CanEditFormPermission
from forms.services import FormService, FormReceiverService, EncryptionKeyService, FormSchemaService
from graphene_permissions.permissions import AllowAuthenticated


class FormNode(DjangoObjectType):
    class Meta:
        model = Form
        filter_fields = ['id']
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


class FormSchemaNone(DjangoObjectType):
    class Meta:
        model = FormSchema
        filter_fields = ['id']
        interfaces = (relay.Node,)


class FormSubmissionNode(PermissionDjangoObjectType):
    class Meta:
        model = FormSubmission
        filter_fields = ['id']
        interfaces = (relay.Node,)

    @classmethod
    @permissions_checker([IsAuthenticated, CanRetrieveFormSubmissionsPermission])
    def get_node(cls, info, id):
        user = get_user_from_info(info)

        try:
            item = FormReceiverService.retrieve_submitted_forms(user).filter(id=id).get()
        except cls._meta.model.DoesNotExist:
            return None
        return item


class EncryptionKeyNode(DjangoObjectType):
    class Meta:
        model = EncryptionKey

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


class Query(graphene.ObjectType):
    # get a single form
    form = relay.Node.Field(FormNode)
    # get a single form submission
    form_submission = relay.Node.Field(FormSubmissionNode)
    # get a list of available forms
    all_forms = DjangoFilterConnectionField(FormNode)
    # get a list of available form submissions
    all_form_submissions = DjangoFilterConnectionField(FormSubmissionNode)
    # get public keys for form
    public_keys_for_form = graphene.List(EncryptionKeyNode, form_id=graphene.ID(required=True))

    def resolve_public_keys_for_form(self, info, form_id):
        return FormService.retrieve_public_keys_for_form(int(from_global_id(form_id)[1]))

    @permissions_checker([IsAuthenticated, CanRetrieveFormSubmissionsPermission])
    def resolve_all_form_submissions(self, info, **kwargs):
        user = get_user_from_info(info)
        return FormReceiverService.retrieve_submitted_forms(user)


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
        return SubmitForm(
            success=True, **result
        )


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
        return SubmitEncryptionKey(
            success=True, encryption_key=result
        )


class CreateFormSchema(FailableMutation):
    form_schema = graphene.Field(FormSchemaNone)

    class Arguments:
        schema = graphene.String(required=True)
        key = graphene.String(required=True)
        form_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanEditFormPermission])
    def mutate(self, info, schema, key, form_id):
        user = get_user_from_info(info)
        try:
            result = FormSchemaService.create_form_schema(user, key, int(from_global_id(form_id)[1]), schema)
        except FormSchemaService.exceptions as e:
            raise MutationExecutionException(str(e))
        return SubmitEncryptionKey(
            success=True, form_schema=result
        )


class UpdateFormSchema(FailableMutation):
    form_schema = graphene.Field(FormSchemaNone)

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
        return SubmitEncryptionKey(
            success=True, form_schema=result
        )


class Mutation(graphene.ObjectType):
    submit_form = SubmitForm.Field()
    submit_encryption_key = SubmitEncryptionKey.Field()
    create_form_schema = CreateFormSchema.Field()
    update_form_schema = UpdateFormSchema.Field()


## Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
