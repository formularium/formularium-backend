import graphene

from forms.schema import Query as forms_query
from teams.schema import Query as teams_query
from forms.schema import Mutation as forms_mutation
from teams.schema import Mutation as teams_mutation
from oauth.schema import schema as oauth_schema


class Query(
    forms_query,
    teams_query,
    oauth_schema.Query,
):
    pass


class Mutation(
    forms_mutation,
    teams_mutation,
    oauth_schema.Mutation,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
