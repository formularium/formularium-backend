from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from forms.models import Form


class UpdateFormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = [
            'name',
            'description',
            'xml_code',
            'js_code',
            'active',
        ]


class CreateFormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = [
            'name',
            'description',
        ]
