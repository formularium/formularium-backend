from serious_django_permissions.groups import Group

from forms.permissions import (
    CanRetrieveFormSubmissionsPermission,
    CanAddEncryptionKeyPermission,
    CanActivateEncryptionKeyPermission,
    CanEditFormPermission,
    CanAddFormTranslationPermission,
)
from teams.permissions import CanCreateTeamPermission, CanRemoveTeamMemberPermission


class AdministrativeStaffGroup(Group):
    permissions = [
        CanRetrieveFormSubmissionsPermission,
        CanAddEncryptionKeyPermission,
        CanAddFormTranslationPermission,
    ]


class InstanceAdminGroup(Group):
    permissions = [
        CanRetrieveFormSubmissionsPermission,
        CanAddEncryptionKeyPermission,
        CanActivateEncryptionKeyPermission,
        CanEditFormPermission,
        CanAddFormTranslationPermission,
        CanRemoveTeamMemberPermission,
        CanCreateTeamPermission,
    ]
