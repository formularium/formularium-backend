from typing import List, Tuple

from collections import Iterable
from datetime import timedelta, datetime
import json
from django.conf import settings

from django.contrib.auth.models import User, AbstractUser, Group
from django.utils.translation import gettext_lazy as _

from serious_django_services import Service, NotPassed, CRUDMixin
import pgpy

from forms.forms import UpdateFormForm, CreateFormForm
from forms.models import SignatureKey, Form, EncryptionKey, FormSubmission, FormSchema
from forms.permissions import CanActivateEncryptionKeyPermission, CanAddEncryptionKeyPermission


class FormServiceException(Exception):
    pass


class FormService(Service, CRUDMixin):
    service_exceptions = (FormServiceException,)

    update_form = UpdateFormForm
    create_form = CreateFormForm

    model = Form

    @classmethod
    def retrieve_form(cls, id: int) -> Form:
        """
        get a form by id
        :param id: id of the form
        :return: the form object
        """
        try:
            form = Form.objects.get(pk=id, active=True)
        except Form.DoesNotExist:
            raise FormServiceException(_("This form doesn't exist or isn't available publicly."))

        return form

    @classmethod
    def retrieve_public_keys_for_form(cls, form_id: int) -> [EncryptionKey]:
        """
        retrieve the public keys the form content should be encrypted with
        :param form_id: id of the form the content is for
        :return: an Iterable of EncryptionKey objects
        """
        form = cls.retrieve_form(form_id)
        return EncryptionKey.objects.filter(
            user__in=User.objects.filter(groups__in=form.teams.all()), active=True)

    @classmethod
    def submit(cls, form_id: int, content: str) -> dict:
        """receives encrypted form data and signs it
          :param form_id: id of the form the content is for
          :param content: pgp encrypted form content
          :returns: object with signed content and the signature
          """

        form = FormService.retrieve_form(form_id)

        # load the signature key
        try:
            # we currently   load the primary key b/c of a bug in pgpy
            signature_key = SignatureKey.objects.filter(active=True,
                                                        key_type=SignatureKey.SignatureKeyType.SECONDARY).get()
            pkey = pgpy.PGPKey()
            pkey.parse(signature_key.private_key)

        except SignatureKey.DoesNotExist:
            raise FormServiceException(_("Couldn't sign form because there are no signing keys available."))

        created_at = datetime.now()
        signed_content = json.dumps({
            "form_data": content,
            "timestamp": created_at.isoformat(),
            "public_key_server": str(pkey.pubkey),
            "public_keys_recipients": [pubkey.public_key for
                                       pubkey in FormService.retrieve_public_keys_for_form(form.pk)],
            "form_id": form.pk,
            "form_name": form.name
        })
        # build the object that should be signed
        with pkey.subkeys[signature_key.subkey_id].unlock(settings.SECRET_KEY):
            signature = pkey.subkeys[signature_key.subkey_id].sign(signed_content)

        FormSubmission.objects.create(signature=signature, data=content, submitted_at=created_at, form=form)

        return {"content": signed_content, "signature": signature}

    @classmethod
    def update_form_(cls, user: AbstractUser,
                     form_id: int,
                     name: str = NotPassed,
                     description: str = NotPassed,
                     xml_code: str = NotPassed,
                     js_code: str = NotPassed,
                     active: bool = NotPassed) -> Form:
        """
        update an exsisting form
        :param user: the user calling the service
        :param form_id: id of the form that should be updated
        :param name: name of the form
        :param description: description (legal information, …)
        :param xml_code: xml code for the visual editor
        :param js_code: javascript code to render the form
        :param active: if the form is active or inactive
        :return: the updated form instance
        """

        # TODO: implement updated note
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to create this form.")

        form = cls._update(form_id, {
            'name': name,
            'description': description,
            'xml_code': xml_code,
            'js_code': js_code,
            'active': active,
        })

        form.refresh_from_db()
        return form

    @classmethod
    def update_form_groups(cls, user: AbstractUser, form_id: int, groups: List[int]) -> Form:
        """
        update the user-groups that receive the form submissions
        :param user: the user calling the service
        :param form_id: the id of the form affected
        :param groups: a list of groups that should be able to receive submissions
        :return: the updated form instance
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to create this form.")

        form = FormService.retrieve_form(form_id)

        form.teams.clear()

        for grp in groups:
            #TODO check team type
            form.teams.add(Group.objects.get(pk=grp))

        form.save()

        return form

    @classmethod
    def create_form_(cls, user: AbstractUser, name: str,
                     description: str) -> Form:
        """
        Create a new form
        :param user: the user calling the service
        :param name: name of the form
        :param description: description (legal information, …)
        :return: the newly created form instance
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to create this form.")

        form = cls._create({
            'name': name,
            'description': description
        })

        return form


class FormSchemaService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def _validate_json_schema(cls, schema: str) -> bool:
        """
        validate if the given string is a valid json schema form
        :param schema: the json schema string
        :return: True if it's valid
        """
        try:
            json.loads(schema)
        except json.JSONDecodeError:
            raise FormServiceException("Not a valid json schema form!")

        return True

    @classmethod
    def create_form_schema(cls, user: AbstractUser, key: str, form_id: int, schema: str) -> FormSchema:
        """
        create a new form section/schema
        :param user: the user calling the service
        :param key: the key this schema uses
        :param form_id: id of the form that uses this schema
        :param schema: the schema object itself
        :return: the newly created schema object
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to create this form schema.")

        form = Form.objects.get(pk=form_id)
        cls._validate_json_schema(schema)
        schema = FormSchema.objects.create(key=key, form=form, schema=schema)
        schema.save()
        return schema

    @classmethod
    def update_form_schema(cls, user: AbstractUser, schema_id: int, schema: str) -> FormSchema:
        """
        :param user: the user calling the service
        :param schema_id: id of the schema that should be updated
        :param schema: the schema object itself
        :return: the updated schema object
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to create this form schema.")

        cls._validate_json_schema(schema)

        form_schema = FormSchema.objects.get(pk=schema_id)
        form_schema.schema = schema
        form_schema.save()

        return form_schema


class FormReceiverService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def retrieve_accessible_forms(cls, user: AbstractUser) -> [Form]:
        """
        Retrieve a list of forms that user can decrypt
        :param user: the user calling the service
        :return: a list of accessible form objects for this user
        """
        return Form.objects.filter(teams__in=user.groups.all())

    @classmethod
    def retrieve_submitted_forms(cls, user: AbstractUser) -> [FormSubmission]:
        """
        retrieve all submitted form obj
        :param user: the user calling the service
        :return: a list of available forms
        """
        accessible_forms = cls.retrieve_accessible_forms(user)
        return FormSubmission.objects.filter(form__in=accessible_forms)


class EncryptionKeyService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def add_key(cls, user: AbstractUser, public_key: str) -> EncryptionKey:
        """
        submit a generated key for a user
        :param user: the user calling the service
        :param public_key: their public key
        :return: id/information about key creation
        """
        if not user.has_perm(CanAddEncryptionKeyPermission):
            raise PermissionError("You are not allowed to add a form key")
        return EncryptionKey.objects.create(user=user, public_key=public_key, active=False)

    @classmethod
    def activate_key(cls, user: AbstractUser, public_key_id) -> EncryptionKey:
        """
        activate a submitted public key, so that newly generated forms use this key for encryption
        :param user: the user calling the service
        :param public_key_id: id the of the public key that should be activated
        :return: the activated key object
        """
        if not user.has_perm(CanActivateEncryptionKeyPermission):
            raise PermissionError("You are not allowed to activate this form key")
        public_key = EncryptionKey.objects.get(id=public_key_id)

        if public_key.active == True:
            raise FormServiceException("This public key is already active.")

        public_key.active = True
        public_key.save()

        return public_key
