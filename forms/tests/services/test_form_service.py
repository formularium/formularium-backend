import json
import pgpy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings

from forms.models import Form, EncryptionKey, SignatureKey
from forms.services import FormService, FormServiceException
from ...management.commands import create_signature_key
from ..utils import generate_test_keypair

class FormReceiverServiceTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="admin")
        self.form = Form.objects.create(name="Hundiformular", description="Doggo", js_code="var foo;",
                                        xml_code="<xml></xml>", active=True)

        # create a group and add a form/user to it
        self.group = Group.objects.create(name="hundigruppe")
        self.user.groups.add(self.group)
        self.form.teams.add(self.group)


    def test_retrieve_pgp_keys_for_form(self):
        # a single key for one user
        keypair = generate_test_keypair()
        first_key = EncryptionKey.objects.create(public_key=keypair["publickey"], user=self.user, active=True)
        keys = FormService.retrieve_public_keys_for_form(self.form.id)
        self.assertEqual(len(keys), 1)

        # multiple keys for the same user
        keypair = generate_test_keypair()
        second_key = EncryptionKey.objects.create(public_key=keypair["publickey"], active=True, user=self.user)
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

        #disable form
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
        first_key = EncryptionKey.objects.create(public_key=keypair["publickey"], user=self.user, active=True)

        with self.assertRaises(FormServiceException):
            FormService.submit(form_id=self.form.id, content="helo")

        create_signature_key.Command().handle()
        result = FormService.submit(form_id=self.form.id, content="helo")
        pub = pgpy.PGPKey()
        pub.parse(SignatureKey.objects.get(active=True,
                                            key_type=SignatureKey.SignatureKeyType.SECONDARY).public_key)

        self.assertEqual(bool(pub.verify(result["content"], result["signature"])), True)
        signed_content = json.loads(result["content"])
        self.assertEqual(signed_content["form_data"], "helo")
        self.assertEqual(len(signed_content["public_keys_recipients"]), 1)
        self.assertEqual(signed_content["public_key_server"],
                         SignatureKey.objects.get(active=True,
                                                  key_type=SignatureKey.SignatureKeyType.SECONDARY).public_key
                         )
        self.assertIn("BEGIN PGP PUBLIC KEY BLOCK", signed_content["public_key_server"])
        self.assertNotIn("BEGIN PGP PRIVATE KEY BLOCK", signed_content["public_key_server"])



