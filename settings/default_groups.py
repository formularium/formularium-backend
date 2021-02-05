from serious_django_permissions.groups import Group

from forms.permissions import CanRetrieveFormSubmissionsPermission, CanAddEncryptionKeyPermission, \
    CanActivateEncryptionKeyPermission


class AdministrativeStaffGroup(Group):
    permissions = [
        CanRetrieveFormSubmissionsPermission,
        CanAddEncryptionKeyPermission
    ]

class InstanceAdminGroup(Group):
    permissions = [
        CanRetrieveFormSubmissionsPermission,
        CanAddEncryptionKeyPermission,
        CanActivateEncryptionKeyPermission,
    ]
