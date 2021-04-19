import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from serious_django_permissions.management.commands import create_groups

from forms.models import Form, EncryptionKey, SignatureKey
from forms.services import FormService, FormServiceException
from settings.default_groups import AdministrativeStaffGroup, InstanceAdminGroup
from ...management.commands import create_signature_key
from ..utils import generate_test_keypair


class FormReceiverServiceTest(TestCase):
    def setUp(self):
        create_groups.Command().handle()

        self.user = get_user_model().objects.create(username="user")
        self.admin = get_user_model().objects.create(username="admin")
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
        self.group = Group.objects.create(name="hundigruppe")
        self.user.groups.add(self.group)
        self.form.teams.add(self.group)

    def test_retrieve_pgp_keys_for_form(self):
        # a single key for one user
        keypair = generate_test_keypair()
        first_key = EncryptionKey.objects.create(
            public_key=keypair["publickey"], user=self.user, active=True
        )
        keys = FormService.retrieve_public_keys_for_form(self.form.id)
        self.assertEqual(len(keys), 1)

        # multiple keys for the same user
        keypair = generate_test_keypair()
        second_key = EncryptionKey.objects.create(
            public_key=keypair["publickey"], active=True, user=self.user
        )
        keys = FormService.retrieve_public_keys_for_form(self.form.id)
        self.assertEqual(len(keys), 2)

        # disable a key
        first_key.active = False
        first_key.save()
        keys = FormService.retrieve_public_keys_for_form(self.form.id)
        self.assertEqual(len(keys), 1)

        # disable a key
        second_key.active = False
        second_key.save()
        keys = FormService.retrieve_public_keys_for_form(self.form.id)
        self.assertEqual(len(keys), 0)

    def test_retrieve_form(self):
        # check form is retrieveable
        form = FormService.retrieve_form(self.form.id)
        self.assertEqual(self.form.id, form.id)

        # disable form
        self.form.active = False
        self.form.save()
        with self.assertRaises(FormServiceException):
            form = FormService.retrieve_form(self.form.id)

        # enable form again
        self.form.active = True
        self.form.save()
        self.assertEqual(self.form.id, form.id)

    def test_submit_form(self):
        keypair = generate_test_keypair()
        first_key = EncryptionKey.objects.create(
            public_key=keypair["publickey"], user=self.user, active=True
        )

        with self.assertRaises(FormServiceException):
            FormService.submit(form_id=self.form.id, content="helo")

        create_signature_key.Command().handle()
        result = FormService.submit(form_id=self.form.id, content="helo")
        pub = pgpy.PGPKey()
        pub.parse(
            SignatureKey.objects.get(
                active=True, key_type=SignatureKey.SignatureKeyType.SECONDARY
            ).public_key
        )

        self.assertEqual(bool(pub.verify(result["content"], result["signature"])), True)
        signed_content = json.loads(result["content"])
        self.assertEqual(signed_content["form_data"], "helo")
        self.assertEqual(len(signed_content["public_keys_recipients"]), 1)
        self.assertEqual(
            signed_content["public_key_server"],
            SignatureKey.objects.get(
                active=True, key_type=SignatureKey.SignatureKeyType.SECONDARY
            ).public_key,
        )
        self.assertIn("BEGIN PGP PUBLIC KEY BLOCK", signed_content["public_key_server"])
        self.assertNotIn(
            "BEGIN PGP PRIVATE KEY BLOCK", signed_content["public_key_server"]
        )

    def test_form_creation(self):
        form = FormService.create_form_(self.admin, "A form", "Hello")
        self.assertEqual(form.description, "Hello")
        self.assertEqual(form.active, False)
        self.assertEqual(Form.objects.count(), 2)

        with self.assertRaises(PermissionError):
            form = FormService.create_form_(self.user, "A form", "Hello")

    def test_form_update(self):
        form = FormService.create_form_(self.admin, "A form", "Hello")
        form = FormService.update_form_(
            self.admin,
            form.pk,
            name="blub",
            active=True,
            js_code="var foo;",
            xml_code="<xml></xml>",
        )
        self.assertEqual(form.xml_code, "<xml></xml>")

        with self.assertRaises(PermissionError):
            form = FormService.update_form_(self.user, form.pk, description="alo")

    def test_update_form_groups(self):
        form = FormService.create_form_(self.admin, "A form", "Hello")
        form = FormService.update_form_(
            self.admin,
            form.pk,
            name="blub",
            active=True,
            js_code="var foo;",
            xml_code="<xml></xml>",
        )
        self.assertEqual(form.xml_code, "<xml></xml>")

        grp = Group.objects.create(name="yolo")

        form = FormService.update_form_groups(self.admin, form.pk, [self.group.pk])
        self.assertEqual(form.teams.first(), self.group)
        self.assertEqual(form.teams.count(), 1)

        form = FormService.update_form_groups(self.admin, form.pk, [grp.pk])
        self.assertEqual(form.teams.first(), grp)
        self.assertEqual(form.teams.count(), 1)

        form = FormService.update_form_groups(
            self.admin, form.pk, [self.group.pk, grp.pk]
        )
        self.assertEqual(form.teams.count(), 2)

        with self.assertRaises(PermissionError):
            form = FormService.update_form_groups(self.user, form.pk, [grp.pk])
