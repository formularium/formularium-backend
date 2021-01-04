from serious_django_permissions.permissions import Permission

from forms.models import FormSubmission, EncryptionKey


class CanRetrieveFormSubmissionsPermission(Permission):
    model = FormSubmission
    description = 'can retrieve form submissions'

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanRetrieveFormSubmissionsPermission)

    @staticmethod
    def has_object_permission(context, obj):
        return True

class CanAddEncryptionKeyPermission(Permission):
    model = EncryptionKey
    description = 'can add a new encryption key'

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanAddEncryptionKeyPermission)

    @staticmethod
    def has_object_permission(context, obj):
        return True