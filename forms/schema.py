import graphene
from graphene import relay, ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from serious_django_graphene import get_user_from_info, FailableMutation, MutationExecutionException
from graphql_relay.node.node import from_global_id

from serious_django_graphene import get_user_from_info, \
    FormMutation, MutationExecutionException
from graphql_relay.node.node import from_global_id
from graphene_django.filter import DjangoFilterConnectionField
from graphene.utils.str_converters import to_snake_case

## Queries
from forms.models import Form, EncryptionKey
from forms.services import FormService



class FormNode(DjangoObjectType):
    class Meta:
        model = Form
        filter_fields = ['id']
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)


class EncryptionKeyNode(DjangoObjectType):
    class Meta:
        model = EncryptionKey

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(active=True)




class Query(graphene.ObjectType):
    # get a single form
    form = relay.Node.Field(FormNode)
    # get a list of available forms
    all_forms = DjangoFilterConnectionField(FormNode)
    # get public keys for form
    public_keys_for_form = graphene.List(EncryptionKeyNode, form_id=graphene.ID(required=True))

    def resolve_public_keys_for_form(self, info, form_id):
        print(FormService.retrieve_public_keys_for_form(int(from_global_id(form_id)[1])))
        return FormService.retrieve_public_keys_for_form(int(from_global_id(form_id)[1]))


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
