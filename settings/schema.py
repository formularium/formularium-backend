import graphene

from forms.schema import Query as forms_query
from forms.schema import Mutation as forms_mutation
from oauth.schema import schema as  oauth_schema

class Query(
    forms_query,
    oauth_schema.Query,
):
    pass


class Mutation(
    forms_mutation,
    oauth_schema.Mutation,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
