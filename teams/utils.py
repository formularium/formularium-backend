import base64
import json
from OpenSSL import crypto
from josepy import JWK

import pem


def cert_to_jwk(certificates: str, public_key: str) -> str:
    """
    coverts a pem public key and a pem certificate chain to a jwk with a x5c element
    :param certificates: the certificates for the x5c as pem key list
    :param public_key: the pem public key as string
    :return: the jwk as string
    """

    # convert public key to jwk
    public_key = crypto.load_publickey(crypto.FILETYPE_PEM, public_key)
    jwk = JWK.load(crypto.dump_publickey(crypto.FILETYPE_PEM, public_key))

    # covert cert chain to base64 encoded ASN1 according to https://tools.ietf.org/html/rfc7517#section-4.7
    x5c = []
    for cert in pem.parse(str.encode(certificates)):
        cert_pem = crypto.load_certificate(crypto.FILETYPE_PEM, cert.as_bytes())
        x5c.append(
            base64.b64encode(
                crypto.dump_certificate(crypto.FILETYPE_ASN1, cert_pem)
            ).decode()
        )

    # dump jwk obj to json and add x5c cer chain
    jwk_j = jwk.to_json()
    jwk_j["x5c"] = x5c
    return json.dumps(jwk_j)
