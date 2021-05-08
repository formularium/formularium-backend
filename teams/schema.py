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

from graphql_relay.node.node import from_global_id
from graphene_django.filter import DjangoFilterConnectionField

from forms.permissions import CanEditFormPermission
from teams.permissions import (
    CanCreateTeamPermission,
)
from teams.models import Team, TeamMembership, TeamRoleChoices

from teams.services import TeamService, TeamMembershipService

from serious_django_graphene import (
    get_user_from_info,
    FormMutation,
    MutationExecutionException,
)


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


class Query(graphene.ObjectType):
    # get a list of available teams
    all_teams = DjangoFilterConnectionField(InternalTeamNode)
    # get a list of available teams
    team = relay.Node.Field(InternalTeamNode)

    @permissions_checker([IsAuthenticated])
    def resolve_all_teams_(self, info, **kwargs):
        user = get_user_from_info(info)
        return Team.objects.all()


class CreateTeam(FailableMutation):
    team = graphene.Field(InternalTeamNode)

    class Arguments:
        name = graphene.String(required=True)
        public_key = graphene.String(required=True)
        key = graphene.String(required=True)
        csr = graphene.String(required=True)

    @permissions_checker([IsAuthenticated, CanCreateTeamPermission])
    def mutate(self, info, name, public_key, key, csr):
        user = get_user_from_info(info)
        try:
            result = TeamService.create(
                user, name=name, public_key=public_key, key=key, csr=csr
            )
        except TeamService.exceptions as e:
            raise MutationExecutionException(str(e))
        return CreateTeam(success=True, team=result)


class AddCertificateForTeam(FailableMutation):
    team = graphene.Field(InternalTeamNode)

    class Arguments:
        certificate = graphene.String(required=True)
        team_id = graphene.ID(required=True)

    @permissions_checker([IsAuthenticated, CanCreateTeamPermission])
    def mutate(self, info, certificate, team_id):
        user = get_user_from_info(info)
        try:
            result = TeamService.add_certificate(
                user, certificate=certificate, team_id=team_id
            )
        except TeamService.exceptions as e:
            raise MutationExecutionException(str(e))
        return AddCertificateForTeam(success=True, team=result)


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


class Mutation(graphene.ObjectType):
    create_team = CreateTeam.Field()
    add_certificate_for_team = AddCertificateForTeam.Field()
    add_team_member = AddTeamMember.Field()
    update_team_member = UpdateTeamMember.Field()
    remove_team_member = RemoveTeamMember.Field()


## Schema

schema = graphene.Schema(query=Query, mutation=Mutation)
