from django.contrib import admin

from forms.models import EncryptionKey, Form, FormSubmission, FormSchema, FormSchemaTemplate

admin.site.register(EncryptionKey)
admin.site.register(Form)
admin.site.register(FormSubmission)
admin.site.register(FormSchema)
admin.site.register(FormSchemaTemplate)