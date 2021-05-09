from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
from serious_django_permissions.management.commands import create_groups

from teams.models import TeamRoleChoices
from teams.services import (
    TeamService,
    TeamServiceException,
    TeamMembershipService,
)
from settings.default_groups import AdministrativeStaffGroup, InstanceAdminGroup


class TeamServiceTest(TestCase):
    def setUp(self):
        create_groups.Command().handle()
        self.user = get_user_model().objects.create(username="adminstaff")
        self.admin = get_user_model().objects.create(username="instanceadmin")
        self.user.groups.add(AdministrativeStaffGroup)
        self.admin.groups.add(InstanceAdminGroup)

    def test_create_team(self):
        team = TeamService.create(self.admin, "Hunditeam", {})
        self.assertEqual(team.name, "Hunditeam")
        self.assertEqual(team.slug, "hunditeam")
        self.assertEqual(team.members.count(), 1)

    def test_create_team_unprivileged_user(self):
        with self.assertRaises(TeamServiceException):
            team = TeamService.create(self.user, "Hunditeam", {})


class TeamMembershipServiceTest(TestCase):
    def setUp(self):
        create_groups.Command().handle()
        self.user = get_user_model().objects.create(username="adminstaff")
        self.admin = get_user_model().objects.create(username="instanceadmin")
        self.user.groups.add(AdministrativeStaffGroup)
        self.admin.groups.add(InstanceAdminGroup)

    def test_add_member(self):
        team = TeamService.create(self.admin, "Hunditeam_", {})
        TeamMembershipService.add_member(self.admin, team.pk, {}, self.user.id)
        team.refresh_from_db()
        self.assertEqual(team.members.count(), 2)

    def test_add_member_unprivileged_user(self):
        team = TeamService.create(self.admin, "Hunditeam_", {})
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.add_member(self.user, team.pk, {}, self.user.id)

    def test_update_member(self):
        team = TeamService.create(self.admin, "Hunditeam__", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        team.refresh_from_db()
        self.assertEqual(team.members.count(), 2)
        TeamMembershipService.update_member(
            self.admin, team.id, self.user.id, role=TeamRoleChoices.ADMIN
        )

    def test_update_member_unprivileged(self):
        team = TeamService.create(self.admin, "Hunditeam__", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.update_member(
                self.user, team.id, self.user.id, role=TeamRoleChoices.ADMIN
            )

    def test_update_member_remove_admin_by_update(self):
        team = TeamService.create(self.admin, "Hunditeam__", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.update_member(
                self.user, team.id, self.user.id, role=TeamRoleChoices.MEMBER
            )

    def test_update_member_not_in_team(self):
        team = TeamService.create(self.admin, "Hunditeam__", {})
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.update_member(
                self.admin, team.id, self.user.id, role=TeamRoleChoices.ADMIN
            )

    def test_update_member_replace_admin_by_update(self):
        team = TeamService.create(self.admin, "Hunditeam__", {})
        TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk, role=TeamRoleChoices.ADMIN
        )
        TeamMembershipService.update_member(
            self.user, team.id, self.admin.id, role=TeamRoleChoices.MEMBER
        )
        self.assertEqual(team.members.count(), 2)

    def test_delete_member(self):
        team = TeamService.create(self.admin, "Hunditeam", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        team.refresh_from_db()
        self.assertEqual(team.members.count(), 2)
        TeamMembershipService.remove_member(self.admin, team.id, self.user.id)
        self.assertEqual(team.members.count(), 1)

    def test_delete_member_unprivileged(self):
        team = TeamService.create(self.admin, "Hunditeam", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        team.refresh_from_db()
        self.assertEqual(team.members.count(), 2)
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.remove_member(self.user, team.id, self.user.id)

    def test_delete_member_remove_admin(self):
        team = TeamService.create(self.admin, "Hunditeam", {})
        membership = TeamMembershipService.add_member(
            self.admin, team.pk, {}, self.user.pk
        )
        team.refresh_from_db()
        self.assertEqual(team.members.count(), 2)
        with self.assertRaises(TeamServiceException):
            TeamMembershipService.remove_member(self.admin, team.id, self.admin.id)
