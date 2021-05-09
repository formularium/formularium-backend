import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from serious_django_permissions.management.commands import create_groups

from forms.models import Form, SignatureKey
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


class FormReceiverServiceTest(TestCase):
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
        self.group = TeamService.create(self.admin, "Hunditeam", {})
        create_mock_cert(self.group)

        TeamMembershipService.add_member(
            self.admin, team_id=self.group.id, keys={}, invited_user_id=self.user.id
        )
        self.form.teams.add(self.group)
        self.keypair = generate_test_keypair()
        self.first_key = EncryptionKey.objects.create(
            public_key=self.keypair["publickey"], user=self.user, active=True
        )
        create_signature_key.Command().handle()
        self.form_submission = FormService.submit(form_id=self.form.id, content="helo")

        self.second_form = Form.objects.create(
            name="andre",
            description="andre",
            js_code="var foo;",
            xml_code="<xml></xml>",
            active=True,
        )
        # create a group and add a form/user to it
        self.second_group = TeamService.create(self.admin, "andre", {})
        create_mock_cert(self.second_group)
        self.second_form.teams.add(self.second_group)
        self.second_form_submission = FormService.submit(
            form_id=self.second_form.id, content="helloo"
        )

    def test_accessible_forms(self):
        self.assertEqual(
            FormReceiverService.retrieve_accessible_forms(self.user).count(), 1
        )
        self.assertEqual(
            FormReceiverService.retrieve_accessible_forms(self.user).first(), self.form
        )

        TeamMembershipService.add_member(
            self.admin,
            self.second_group.id,
            keys={1: "cfvrgvr"},
            invited_user_id=self.user.pk,
        )
        self.assertEqual(
            FormReceiverService.retrieve_accessible_forms(self.user).count(), 2
        )

    def test_retrieve_form_submissions(self):
        self.assertEqual(
            FormReceiverService.retrieve_submitted_forms(self.user).count(), 1
        )
        FormService.submit(form_id=self.form.id, content="helo")
        self.assertEqual(
            FormReceiverService.retrieve_submitted_forms(self.user).count(), 2
        )

        TeamMembershipService.add_member(
            self.admin,
            self.second_group.id,
            keys={1: "jencejkfcnejk"},
            invited_user_id=self.user.pk,
        )

        self.assertEqual(
            FormReceiverService.retrieve_submitted_forms(self.user).count(), 3
        )
