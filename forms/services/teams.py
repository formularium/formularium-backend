from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from serious_django_services import Service, CRUDMixin, NotPassed

from forms.forms import (
    CreateTeamForm,
    UpdateTeamForm,
    CreateTeamMembershipForm,
    UpdateTeamMembershipForm,
)
from forms.models import Team, TeamRoleChoices, TeamMembership
from forms.permissions import CanCreateTeamPermission, CanRemoveTeamMemberPermission


class TeamServiceException(Exception):
    pass


class TeamService(Service, CRUDMixin):
    service_exceptions = (TeamServiceException,)

    update_form = UpdateTeamForm
    create_form = CreateTeamForm

    model = Team

    @classmethod
    def create(cls, user: AbstractUser, name: str, key: str, public_key: str) -> Team:
        """
        creates a new user and makes them admin
        :param public_key: public key for this team
        :param user: user calling the service (needs CanCreateTeamPermission permission)
        :param name: name of the Team
        :param key: the newly generated public key
        :return: the newly generated team
        """
        if not user.has_perm(CanCreateTeamPermission):
            raise TeamServiceException(
                "You don't have the permission to create a new team"
            )

        team = cls._create(
            {"name": name, "slug": slugify(name), "public_key": public_key}
        )

        TeamMembershipService.add_member(
            user=user,
            team_id=team.id,
            key=key,
            invited_user_id=user.id,
            role=TeamRoleChoices.ADMIN,
        )
        return team

    @classmethod
    def retrieve(cls, user, id: int) -> Team:
        """
        retrieve a team object
        :param user: user calling the service
        :param id: id of the team
        :return: team object
        """
        return cls._retrieve(id)


class TeamMembershipService(Service, CRUDMixin):
    service_exceptions = (TeamServiceException,)

    update_form = UpdateTeamMembershipForm
    create_form = CreateTeamMembershipForm

    model = TeamMembership

    @classmethod
    def add_member(
        cls,
        user: AbstractUser,
        team_id: int,
        key: str,
        invited_user_id: int,
        role: TeamRoleChoices = TeamRoleChoices.MEMBER,
    ) -> TeamMembership:
        """
        creates a new user and makes them admin
        :param invited_user_id: the user that sould be added
        :param role: the role the newly created Member should have (Admin or Member)
        :param team_id: the id of the team the user should be added to
        :param user: user calling the services (needs CanCreateTeamPermission permission)
        :param key: the newly generated public key
        :return: the newly generated team
        """

        team = TeamService.retrieve(user, team_id)

        if (
            not (
                user.has_perm(CanCreateTeamPermission)
                and team.members.count() == 0
                and invited_user_id == user.pk
            )
            and not team.members.filter(user=user, role=TeamRoleChoices.ADMIN).exists()
        ):
            raise TeamServiceException(
                "You don't have the permission to create a new team"
            )

        team_membership = cls._create(
            {
                "team": team_id,
                "key": key,
                "user": invited_user_id,
                "role": role,
            }
        )

        return team_membership

    @classmethod
    def update_member(
        cls,
        user: AbstractUser,
        team_id: int,
        affected_user_id: int,
        key: str = NotPassed,
        role: TeamRoleChoices = NotPassed,
    ) -> TeamMembership:
        """
        update a team member
        :param user: the user calling the serviceis affected
        :param key: the new encrypted key for this user
        :param affected_user_id: the user that affects this change
        :param role: role of the user
        :return: team membership object
        """
        team = TeamService.retrieve(user, team_id)

        if not team.members.filter(user=user, role=TeamRoleChoices.ADMIN).exists():
            raise TeamServiceException(
                "You don't have the permission to edit a team member."
            )

        if not team.members.filter(user=affected_user_id).exists():
            raise TeamServiceException(
                "This user is not in the team you want to change."
            )

        membership = team.members.filter(user=affected_user_id).get()

        if (
            role == TeamRoleChoices.MEMBER
            and membership.role == TeamRoleChoices.ADMIN
            and team.members.filter(role=TeamRoleChoices.ADMIN).count() == 1
        ):
            raise TeamServiceException(
                "This user can't become a member because every team needs at least one admin."
            )

        cls._update(
            membership.id,
            {
                "key": key,
                "role": role,
            },
        )
        membership.refresh_from_db()
        return membership

    @classmethod
    def remove_member(
        cls, user: AbstractUser, team_id: int, affected_user_id: int
    ) -> bool:
        """
        update a team member
        :param user: user calling the service
        :param team_id: id of the team the user should be removed from
        :param affected_user_id: the user that should be removed
        :return: True if user has been sucessfully removed
        """

        team = TeamService.retrieve(user, team_id)

        if not team.members.filter(
            user=user, role=TeamRoleChoices.ADMIN
        ).exists() and not user.has_perm(CanRemoveTeamMemberPermission):
            raise TeamServiceException(
                "You don't have the permission to remove a team member."
                "You must be either team admin or have the permission 'CanRemoveTeamMemberPermission'."
            )

        membership = team.members.filter(user=affected_user_id).get()

        if (
            team.members.filter(role=TeamRoleChoices.ADMIN).count() == 1
            and membership.role == TeamRoleChoices.ADMIN
        ):
            raise TeamServiceException(
                "This user can't be removed because every team needs at least one admin."
            )

        return cls._delete(membership.id)
