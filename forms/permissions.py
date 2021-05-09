from serious_django_permissions.permissions import Permission

from forms.models import FormSubmission, Form


class CanRetrieveFormSubmissionsPermission(Permission):
    model = FormSubmission
    description = "can retrieve form submissions"

    @staticmethod
    def has_permission(context):
        return context.user.has_perm(CanRetrieveFormSubmissionsPermission)

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
