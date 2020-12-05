from datetime import timedelta, datetime
import json

from django.contrib.auth.models import User

from serious_django_services import Service
import pgpy

from forms.models import SignatureKey, Form, EncryptionKey, FormSubmission


class FormServiceSpecificException(Exception):
    pass


class FormService(Service):
    service_exceptions = (FormServiceSpecificException,)

    @classmethod
    def retrieve_form(cls, id: int) -> Form:
        """
        get a form by id
        :param id: id of the form
        :return: the form object
        """
        return Form.objects.get(pk=id, active=True)


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
        """receives encrypted form data and signs them
          :param form_id: id of the form the content is for
          :param content: pgp encrypted form content
          :returns: object with signed content and the signature
          """

        form = FormService.retrieve_form(form_id)

        # load the signature key
        key = pgpy.PGPKey()
        key.parse(SignatureKey.objects.filter(active=True,
                                              key_type=SignatureKey.SignatureKeyType.SECONDARY).get().private_key)

        created_at = datetime.now()

        # build the object that should be signed
        signed_content = json.dumps({
                "form_data": content,
                "timestamp": created_at.isoformat(),
                "public_key_server": str(key.pubkey),
                "public_keys_recipients": [pubkey.public_key for
                                           pubkey in FormService.retrieve_public_keys_for_form(form.pk)],
                "form_id": form.pk,
                "form_name": form.name
        })
        signature = key.sign(signed_content)

        FormSubmission.objects.create(signature=signature, data=content, submitted_at=created_at, form=form)

        return {"content":  signed_content, "signature": signature}