from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Create your forms here.
#
# ValidationError and _ are imported so you can raise auto-translated errors
# inside custom validation functions.
from teams.models import Team, TeamMembership, EncryptionKey


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = [
            "name",
        ]


class UpdateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name"]


class CreateEncryptionKeyForm(forms.ModelForm):
    class Meta:
        model = EncryptionKey
        fields = ["user", "key_name", "public_key"]


class UpdateEncryptionKeyForm(forms.ModelForm):
    class Meta:
        model = EncryptionKey
        fields = ["key_name"]


class CreateTeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = ["user", "team", "role"]


class UpdateTeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = [
            "role",
        ]
