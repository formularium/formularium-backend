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
    key_type = models.TextField(choices=SignatureKeyType.choices, max_length=20)
    active = models.BooleanField()

    def __str__(self):
        return self.public_key


class Form(models.Model):
    name = models.CharField(max_length=100)
    xml_code = models.TextField()
    js_code = models.TextField()
    active = models.BooleanField()
    teams = models.ManyToManyField(Group)  # teams that can decrypt the submissions

    def __str__(self):
        return self.name


class FormSubmission(models.Model):
    data = models.TextField()
    description = models.TextField(blank=True)
    signature = models.TextField()
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.form} ({self.submitted_at})'
