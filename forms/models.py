import json
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _


class EncryptionKey(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    public_key = models.TextField()
    active = models.BooleanField()

    def __str__(self):
        return self.user.username


class SignatureKey(models.Model):
    class SignatureKeyType(models.TextChoices):
        PRIMARY = 'primary', _('Primary')
        SECONDARY = 'secondary', _('Secondary')

    public_key = models.TextField()
    private_key = models.TextField()
    subkey_id = models.CharField(max_length=255, blank=True)
    key_type = models.TextField(choices=SignatureKeyType.choices, max_length=20)
    active = models.BooleanField()

    def __str__(self):
        return self.public_key


class FormSchemaTemplateTypeChoices(models.TextChoices):
    FORM_FIELD = "field", _("Form Field")
    FORM_SECTION = "section", _("Form Section")


class FormSchemaTemplate(models.Model):
    type = models.CharField(
        max_length=10,
        choices=FormSchemaTemplateTypeChoices.choices,
        default=FormSchemaTemplateTypeChoices.FORM_SECTION,
    )
    schema = models.TextField()
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Form(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    xml_code = models.TextField()
    js_code = models.TextField()
    active = models.BooleanField()
    teams = models.ManyToManyField(Group, related_name='forms')  # teams that can decrypt the submissions

    @property
    def generated_schema(self):
        schema = {}
        for e in self.schemas:
            schema[e.name] = json.loads(e.schema)

        return schema

    def __str__(self):
        return self.name


class FormSchema(models.Model):
    key = models.CharField(max_length=100)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='schemas')
    # we don't use a json field here because its not supported in sqlite
    schema = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['key', 'form'], name='unique_key_per_form'),
        ]

    def __str__(self):
        return self.key


class FormSubmission(models.Model):
    data = models.TextField()
    signature = models.TextField()
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.form} ({self.submitted_at})'
