from serious_django_permissions.groups import Group

from forms.permissions import CanRetrieveFormSubmissionsPermission


class AdministrativeStaffGroup(Group):
    permissions = [
        CanRetrieveFormSubmissionsPermission
    ]
