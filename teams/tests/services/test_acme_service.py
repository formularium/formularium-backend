import OpenSSL
from acme import crypto_util
from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
from serious_django_permissions.management.commands import create_groups

from settings.default_groups import AdministrativeStaffGroup, InstanceAdminGroup
from teams.services import ACMEService

CERT_PKEY_BITS = 2048


def new_csr_comp(domain_name, pkey_pem=None):
    """Create certificate signing request."""
    if pkey_pem is None:
        # Create private key.
        pkey = OpenSSL.crypto.PKey()
        pkey.generate_key(OpenSSL.crypto.TYPE_RSA, CERT_PKEY_BITS)
        pkey_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey)
    csr_pem = crypto_util.make_csr(pkey_pem, [domain_name])
    return pkey_pem, csr_pem


class ACMEServiceTest(TestCase):
    def setUp(self):
        create_groups.Command().handle()
        self.user = get_user_model().objects.create(username="adminstaff")
        self.admin = get_user_model().objects.create(username="instanceadmin")
        self.user.groups.add(AdministrativeStaffGroup)
        self.admin.groups.add(InstanceAdminGroup)

    def test_create_account(self):
        acme = ACMEService.register_account(
            "mail@lilithwittmann.de",
            directory_url="https://acme-staging-v02.api.letsencrypt.org/directory",
        )
        pkey_pem, csr = new_csr_comp("example.foo.formularium.de")
        challenge, validation = acme.new_order(csr)
        self.assertIn(challenge, validation)
        print(challenge)
