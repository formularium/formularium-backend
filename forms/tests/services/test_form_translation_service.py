import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from serious_django_permissions.management.commands import create_groups

from forms.models import Form, EncryptionKey, SignatureKey, FormSchema
from forms.services.forms import (
    FormService,
    FormServiceException,
    FormReceiverService,
    EncryptionKeyService,
    FormSchemaService,
    FormTranslationService,
)
from teams.services import TeamService, TeamMembershipService
from settings.default_groups import AdministrativeStaffGroup, InstanceAdminGroup
from teams.tests.services.mock import create_mock_cert
from ...management.commands import create_signature_key
from ..utils import generate_test_keypair


class FormSchemaServiceTest(TestCase):
    def setUp(self):
        create_groups.Command().handle()
        self.user = get_user_model().objects.create(username="adminstaff")
        self.admin = get_user_model().objects.create(username="instanceadmin")
        self.user.groups.add(AdministrativeStaffGroup)
        self.admin.groups.add(InstanceAdminGroup)

        self.form = Form.objects.create(
            name="Hundiformular",
            description="Doggo",
            js_code="var foo;",
            xml_code="<xml></xml>",
            active=True,
        )

        # create a group and add a form/user to it
        self.group = TeamService.create(self.admin, "Hunditeam", "fefecsdcsd")
        create_mock_cert(self.group)

        TeamMembershipService.add_member(
            self.admin, team_id=self.group.id, key="dcdcd", invited_user_id=self.user.id
        )
        self.form.teams.add(self.group)
        self.keypair = generate_test_keypair()
        self.first_key = EncryptionKey.objects.create(
            public_key=self.keypair["publickey"], user=self.user, active=True
        )
        create_signature_key.Command().handle()
        self.form_submission = FormService.submit(form_id=self.form.id, content="helo")

    def test_add_translation(self):
        translation = FormTranslationService.create_form_translation(
            self.user, form_id=self.form.id, language="de", region="DE"
        )
        self.assertEqual(translation.language, "de")

        with self.assertRaises(FormServiceException):
            translation = FormTranslationService.create_form_translation(
                self.user, form_id=self.form.id, language="NOTALanguage", region="DE"
            )

    def test_update_translation(self):
        translation = FormTranslationService.create_form_translation(
            self.user, form_id=self.form.id, language="de", region="DE"
        )
        self.assertEqual(translation.language, "de")
        self.assertEqual(translation.active, False)
        translation = FormTranslationService.update_form_translation(
            self.user,
            translation_id=translation.id,
            language="en",
            region="US",
            active=True,
        )
        self.assertEqual(translation.language, "en")
        self.assertEqual(translation.active, True)

    def test_update_translation_key(self):
        translation = FormTranslationService.create_form_translation(
            self.user, form_id=self.form.id, language="en", region="US"
        )
        translated_key = FormTranslationService.update_translation_string(
            user=self.user,
            translation_id=translation.pk,
            key="a.greeting",
            value="Hey there!",
        )

        self.assertEqual(translated_key.value, "Hey there!")
