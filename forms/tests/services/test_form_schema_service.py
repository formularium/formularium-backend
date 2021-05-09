import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from serious_django_permissions.management.commands import create_groups

from forms.models import Form, SignatureKey, FormSchema
from forms.services.forms import (
    FormService,
    FormServiceException,
    FormReceiverService,
    FormSchemaService,
)
from teams.models import EncryptionKey
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

    def test_form_schema_creation(self):
        schema = FormSchemaService.create_form_schema(
            self.admin, "sction", self.form.id, '{"acab": true}'
        )
        self.assertEqual(FormSchema.objects.count(), 1)

    def test_form_schema_update(self):
        schema = FormSchemaService.create_form_schema(
            self.admin, "sction", self.form.id, '{"acab": true}'
        )
        self.assertEqual(FormSchema.objects.count(), 1)
        self.assertEqual(schema.schema, '{"acab": true}')

        schema = FormSchemaService.update_form_schema(
            self.admin, schema.pk, '{"acab": false}'
        )
        self.assertEqual(FormSchema.objects.count(), 1)
        self.assertEqual(schema.schema, '{"acab": false}')

    def test_create_or_update(self):
        schema = FormSchemaService.create_or_update_form_schema(
            self.admin, "sction", self.form.id, '{"acab": true}'
        )
        schema_update = FormSchemaService.create_or_update_form_schema(
            self.admin, "sction", self.form.id, '{"allo": true}'
        )

        self.assertEqual(schema.pk, schema_update.pk)
        self.assertEqual(schema_update.schema, '{"allo": true}')
