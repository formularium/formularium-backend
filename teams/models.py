from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# Create your models here.


class TeamStatus(models.TextChoices):
    ACTIVE = "active", _("active")
    WAITING_FOR_CERTIFICATE = "waiting for certificate", _("waiting for certificate")


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def public_key(self):
        # TODO: this is an ugly hack til refactoring is done
        return self.certificates.filter(status=TeamStatus.ACTIVE).first().public_key


class TeamCertificate(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="certificates"
    )
    public_key = models.TextField()
    csr = models.TextField()
    certificate = models.TextField(null=True)
    status = models.CharField(
        choices=TeamStatus.choices,
        default=TeamStatus.WAITING_FOR_CERTIFICATE,
        max_length=30,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class TeamACMEAccount(models.Model):
    team = models.OneToOneField(
        Team, on_delete=models.CASCADE, related_name="acme_account"
    )
    email = models.CharField(max_length=255)
    jwk = models.TextField()


class TeamRoleChoices(models.TextChoices):
    MEMBER = "member", _("Member")
    ADMIN = "admin", _("Admin")


class TeamMembership(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="memberships"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    member_since = models.DateTimeField(auto_now_add=True)
    role = models.CharField(choices=TeamRoleChoices.choices, max_length=9)
    key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
