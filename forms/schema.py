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
from forms.models import Form, EncryptionKey, FormSubmission
from forms.permissions import CanRetrieveFormSubmissionsPermission
from forms.services import FormService, FormReceiverService
from graphene_permissions.permissions import AllowAuthenticated


class FormNode(DjangoObjectType):
    class Meta:
        model = Form
        filter_fields = ['id']
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


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



class Mutation(graphene.ObjectType):
    submit_form = SubmitForm.Field()


## Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
