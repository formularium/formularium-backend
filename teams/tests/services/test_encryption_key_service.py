import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from serious_django_permissions.management.commands import create_groups

from forms.management.commands import create_signature_key
from forms.models import Form, SignatureKey
from forms.services.forms import (
    FormService,
)
from forms.tests.utils import generate_test_keypair
from teams.models import EncryptionKey
from teams.services import TeamService, TeamMembershipService, EncryptionKeyService
from settings.default_groups import AdministrativeStaffGroup, InstanceAdminGroup
from teams.tests.services.mock import create_mock_cert


class EncryptionKeyServiceTest(TestCase):
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

    def test_submit_key(self):
        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )
        key = EncryptionKeyService.add_key(self.user, "keeey")
        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )
        key.active = True
        key.save()
        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )

    def test_activate_key(self):
        key = EncryptionKeyService.add_key(self.user, "keeey")
        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )

        key = EncryptionKeyService.activate_key(self.admin, key.id)

        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )

        key_two = EncryptionKeyService.add_key(self.user, "keeey")
        self.assertEqual(
            len(FormService.retrieve_public_keys_for_form(self.form.id)), 1
        )

        with self.assertRaises(PermissionError):
            key_two = EncryptionKeyService.activate_key(self.user, key_two)
