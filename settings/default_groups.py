from serious_django_permissions.groups import Group

from forms.permissions import (
    CanRetrieveFormSubmissionsPermission,
    CanAddEncryptionKeyPermission,
    CanActivateEncryptionKeyPermission,
    CanEditFormPermission,
    CanAddFormTranslationPermission,
    CanRemoveTeamMemberPermission,
    CanCreateTeamPermission,
)


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
