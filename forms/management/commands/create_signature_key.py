from django.core.management.base import BaseCommand

from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
import pgpy
from datetime import timedelta

from forms.models import SignatureKey


class Command(BaseCommand):
    """
    A command to generate public/private signature keys for confirmation of receipt of forms
    """
    help = 'A command to generate public/private signature keys for confirmation of receipt of forms'

    def handle(self, *args, **options):
        # we can start by generating a primary key. For this example, we'll use RSA, but it could be DSA or ECDSA as well
        key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)

        # TODO this should be configured via cli on key generation
        # we now have some key material, but our new key doesn't have a user ID yet, and therefore is not yet usable!
        uid = pgpy.PGPUID.new('Formularium@domain')

        # now we must add the new user id to the key. We'll need to specify all of our preferences at this point
        # because PGPy doesn't have any built-in key preference defaults at this time
        # this example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
        # We only configure the key for signing so hopefully nobody will use this for anything else.
        key.add_uid(uid, usage={KeyFlags.Sign},
                    hashes=[HashAlgorithm.SHA512],
                    ciphers=[SymmetricKeyAlgorithm.AES256],
                    compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP,
                                 CompressionAlgorithm.Uncompressed], key_expires=timedelta(days=365))

        #generate and add the subkey
        subkey = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
        key.add_subkey(subkey, usage={KeyFlags.Sign})

        # Before we add the new key we disable all other old key because there can be only one active signature key for now
        SignatureKey.objects.filter(active=True).update(active=False)

        # TODO: storing the private key in the database is actually a bad idea. (better use TPMS, …)
        SignatureKey.objects.create(public_key=str(key.pubkey), private_key=str(key),
                                    key_type=SignatureKey.SignatureKeyType.PRIMARY, active=True)
        SignatureKey.objects.create(public_key=str(subkey.pubkey), private_key=str(key),
                                    key_type=SignatureKey.SignatureKeyType.SECONDARY, active=True)
        print(str(subkey.pubkey))
        # assuming we already have a primary key, we can generate a new key and add it as a subkey thusly:



