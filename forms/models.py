from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class EncryptionKey(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    public_key = models.TextField()

class SignatureKey(models.Model):
    public_key = models.TextField()
    private_key = models.TextField()

class Form(models.Model):
    name = models.CharField(max_length=100)
    xml_code = models.TextField()
    js_code = models.TextField()
    active = models.BooleanField()
    teams = models.ManyToManyField(Group) # teams that can decrypt the submissions

class FormSubmission(models.Model):
    data = models.TextField()
    signature = models.TextField()
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)