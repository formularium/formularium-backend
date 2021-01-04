from datetime import timedelta, datetime
import json
from django.conf import settings

from django.contrib.auth.models import User, AbstractUser
from django.utils.translation import gettext_lazy as _

from serious_django_services import Service
import pgpy

from forms.models import SignatureKey, Form, EncryptionKey, FormSubmission


class FormServiceException(Exception):
    pass


class FormService(Service):
    service_exceptions = (FormServiceException,)

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


class FormReceiverService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def retrieve_accessible_forms(cls, user: AbstractUser) -> [Form]:
        return Form.objects.filter(teams__in=user.groups.all())

    @classmethod
    def retrieve_submitted_forms(cls, user: AbstractUser) -> [FormSubmission]:
        accessible_forms = cls.retrieve_accessible_forms(user)
        return FormSubmission.objects.filter(form__in=accessible_forms)


class EncryptionKeyService(Service):
    service_exceptions = (FormServiceException,)

    @classmethod
    def add_key(cls, user: AbstractUser, public_key: str) -> EncryptionKey:
        return EncryptionKey.objects.create(user=user, public_key=public_key, active=True)
