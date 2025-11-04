from apps.payment.helpers.generating_private_public_key_helpers import to_pem

import os

from dotenv import load_dotenv
load_dotenv()

MerchantPrivateKey = to_pem(
    os.environ['CHEEZEE_PAY_PRIVATE_KEY'],
    "PRIVATE KEY"
)

PlatformPublicKey = to_pem(
    os.environ['CHEEZEE_PAY_PUBLIC_KEY'],
    "PUBLIC KEY"
)

CryptoPrivateKey = to_pem(
    os.environ['CHEEZEE_PAY_PRIVATE_KEY'],
    "PRIVATE KEY"
)

CryptoPublickey = to_pem(
    os.environ['CHEEZEE_PAY_PUBLIC_KEY'],
    "PUBLIC KEY"
)


headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/93.0.4577.63 Safari/537.36",
            "Content-Type": "application/json"
        }