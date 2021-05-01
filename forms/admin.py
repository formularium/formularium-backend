from django.contrib import admin

from forms.models import (
    EncryptionKey,
    Form,
    FormSubmission,
    FormSchema,
    FormSchemaTemplate,
    FormTranslation,
    TranslationKey,
    TeamMembership,
    Team,
)

admin.site.register(EncryptionKey)
admin.site.register(Form)
admin.site.register(FormSubmission)
admin.site.register(FormSchema)
admin.site.register(FormSchemaTemplate)


class TranslationKeyInline(admin.TabularInline):
    model = TranslationKey


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership


class FormTranslationAdmin(admin.ModelAdmin):
    inlines = [TranslationKeyInline]


class TeamAdmin(admin.ModelAdmin):
    inlines = [TeamMembershipInline]


admin.site.register(FormTranslation, FormTranslationAdmin)
admin.site.register(Team, TeamAdmin)
