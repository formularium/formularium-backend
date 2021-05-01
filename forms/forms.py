from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from forms.models import Form, FormTranslation, TranslationKey, Team, TeamMembership


class UpdateFormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = [
            "name",
            "description",
            "xml_code",
            "js_code",
            "active",
        ]


class CreateFormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = [
            "name",
            "description",
        ]


class CreateFormTranslationForm(forms.ModelForm):
    class Meta:
        model = FormTranslation
        fields = ["form", "language", "region"]


class UpdateFormTranslationForm(forms.ModelForm):
    class Meta:
        model = FormTranslation
        fields = ["form", "language", "region", "active"]


class CreateTranslationKeyForm(forms.ModelForm):
    class Meta:
        model = TranslationKey
        fields = [
            "translation",
            "key",
            "value",
        ]


class UpdateTranslationKeyForm(forms.ModelForm):
    class Meta:
        model = TranslationKey
        fields = [
            "translation",
            "key",
            "value",
        ]


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "slug", "public_key"]


class UpdateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "public_key"]


class CreateTeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = [
            "user",
            "team",
            "role",
            "key",
        ]


class UpdateTeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = [
            "role",
            "key",
        ]
