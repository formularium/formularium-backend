from django.test import TestCase

from serious_django_permissions.management.commands import create_groups
from serious_django_graphene.testing import GrapheneAPITest,\
    GrapheneMutationTest, GrapheneFormMutationTest

### Define your tests here.
# EXAMPLE:

# class SomeModelTest(TestCase):
#     def test_creation(self):
#         self.assertTrue(SomeModel.create().created)
#
#
# class SomeGrapheneTest(GrapheneAPITest):
#     schema_src = 'some_app.schema.schema'
#
#     def setUp(self):
#         create_groups.Command().handle()
#         self.some_user = User.objects.first()
#
#     def test_something(self):
#         query = """{ getSomething { id } }"""
#         self.assertExecuteReturns(query, {'data': {'something': [] }}, user=some_user)
#         pass
#
#
# class SomeFormMutationTest(GrapheneFormMutationTest):
#     schema_src = 'some_app.schema.schema'
#     gql_mutation_name = 'someMutation'
#     mutation = """
#     mutation($someVariable: String) {
#       someMutation {
#         success
#         error {
#           ... on ValidationErrors { validationErrors { messages, field } }
#           ... on ExecutionError { errorMessage }
#         }
#         someField {
#           id
#         }
#       }
#     }
#     """
#
#     def test_something(self):
#         result = self.mutate(user=self.some_user, variables={
#             'someVariable': "something"
#         })
#         self.assertSuccessful(result)
