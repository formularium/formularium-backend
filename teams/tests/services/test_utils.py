import json
from django.test import TestCase, RequestFactory

from teams.tests.services.mock import TEST_CERT, TEST_PUBLIC_KEY
from teams.utils import cert_to_jwk


class TestUtils(TestCase):
    def test_certificate_to_jwk(self):
        result = json.loads(cert_to_jwk(TEST_CERT, TEST_PUBLIC_KEY))
        self.assertEqual(
            result["n"],
            "lKigeZEO_FUQbQmlMrN5tHmL1v7QPpvU48dGFZWAmuu5Iie-MXxRKH5yeOw3B16sJBlI5jAN3-12hKLOVj5Guco3RZ9PtulTlZ9WKjHlz7g5O3sLBB7RuThxkR_ovxTHtfFQ0DzNRAxiKrWnOs3C7o5N553ASbq8jK3EaNi_ijKHyH1n9fhbH7lHoIiEN85DQpmIx4cjktCHEbMOEba3edqCLEb6ijVnnsDo13tszFpYdHoMvY4iFgjQ6yvO2clmGjRElwFiDoUDZbvq7gZ2MGwh1QgTUVP8OGGAFFeEp-sVo6TwvIfo0HeL0qQ1YS2T6WDO-LKQr65CDLq00rZCQQ",
        )
        self.assertEqual(len(result["x5c"]), 3)
        self.assertEqual(result["kty"], "RSA")
