from django.contrib import admin

from forms.models import EncryptionKey, Form, FormSubmission

admin.site.register(EncryptionKey)
admin.site.register(Form)
admin.site.register(FormSubmission)