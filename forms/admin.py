from django.contrib import admin

from forms.models import (
    EncryptionKey,
    Form,
    FormSubmission,
    FormSchema,
    FormSchemaTemplate,
    FormTranslation,
    TranslationKey,
)

admin.site.register(EncryptionKey)
admin.site.register(Form)
admin.site.register(FormSubmission)
admin.site.register(FormSchema)
admin.site.register(FormSchemaTemplate)


class TranslationKeyInline(admin.TabularInline):
    model = TranslationKey


class FormTranslationAdmin(admin.ModelAdmin):
    inlines = [TranslationKeyInline]


admin.site.register(FormTranslation, FormTranslationAdmin)
