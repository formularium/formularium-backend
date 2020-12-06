from django.core.management.base import BaseCommand

from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
import pgpy
from datetime import timedelta
from django.conf import settings
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

        SignatureKey.objects.filter(active=True).update(active=False)

        # TODO: in the future we should generate a primary key which is the parent of the subkey. This primary should be protected
        # with a password only known to the admin while the secondary key is unlocked with the django secret key
        # this means that s.b. with only access to the database can steal the keys but unlock them

        for key_id, registered_subkey in key.subkeys.items():
            current_key = key
            current_key.protect(settings.SECRET_KEY, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
            SignatureKey.objects.create(public_key=str(current_key.pubkey), private_key=str(current_key), subkey_id=key_id,
                                              key_type=SignatureKey.SignatureKeyType.SECONDARY, active=True)




