import datetime
import pgpy
from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# Create your models here.
from teams.utils import cert_to_jwk, get_cert_valid_until


class EncryptionKey(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="encryption_keys"
    )
    key_name = models.CharField(max_length=200, default="", blank=True)
    public_key = models.TextField()
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def fingerprint(self) -> str:
        pkey = pgpy.PGPKey()
        pkey.parse(self.public_key)
        return pkey.fingerprint

    def __str__(self):
        return f"{self.fingerprint} ({self.user.username})"


class TeamStatus(models.TextChoices):
    ACTIVE = "active", _("active")
    WAITING_FOR_CERTIFICATE = "waiting for certificate", _("waiting for certificate")


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from="name")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def domain(self) -> str:
        return f"{self.slug}.{settings.CERTIFICATE_DOMAIN}"

    @property
    def public_key(self) -> str:
        certificate = self.certificates.filter(status=TeamStatus.ACTIVE).first()
        if certificate:
            return cert_to_jwk(certificate.certificate, certificate.public_key)
        return None

    def __str__(self):
        return self.name


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

    @property
    def valid_until(self) -> datetime:
        certificate = self.certificate
        if certificate:
            return get_cert_valid_until(certificate)
        return None

    def __str__(self):
        return f"{self.team} ({self.status})"


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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team} - {self.user}"


class TeamMembershipAccessKey(models.Model):
    membership = models.ForeignKey(
        TeamMembership, on_delete=models.CASCADE, related_name="access_keys"
    )
    key = models.TextField()
    encryption_key = models.ForeignKey(
        EncryptionKey, on_delete=models.CASCADE, related_name="access_keys"
    )
