from serious_django_permissions.permissions import Permission

from forms.models import FormSubmission, EncryptionKey, Form, Team


class CanRetrieveFormSubmissionsPermission(Permission):
    model = FormSubmission
    description = "can retrieve form submissions"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanRetrieveFormSubmissionsPermission)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanAddEncryptionKeyPermission(Permission):
    model = EncryptionKey
    description = "can add a new encryption key"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanAddEncryptionKeyPermission)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanActivateEncryptionKeyPermission(Permission):
    model = EncryptionKey
    description = "can activate a new encryption key"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanActivateEncryptionKeyPermission)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanEditFormPermission(Permission):
    model = Form
    description = "can activate a new encryption key"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(Form)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanAddFormTranslationPermission(Permission):
    model = Form
    description = "can add a new form translation"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(Form)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanCreateTeamPermission(Permission):
    model = Team
    description = "can create a new team"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(Form)

    @staticmethod
    def has_object_permission(context, obj):
        return True


class CanRemoveTeamMemberPermission(Permission):
    model = Team
    description = "can remove team members from all teams"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(Form)

    @staticmethod
    def has_object_permission(context, obj):
        return True
