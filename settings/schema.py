import graphene

from forms.schema import Query as forms_query
from forms.schema import Mutation as forms_mutation
class Query(
    forms_query,
):
    pass


class Mutation(
    forms_mutation,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
