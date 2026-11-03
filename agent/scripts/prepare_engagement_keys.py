"""Generate local notification secrets without printing or overwriting them."""
import argparse
import base64
import os
from pathlib import Path
import secrets

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid02


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Ignored private environment file; must not exist")
    args = parser.parse_args()
    target = Path(args.output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    vapid = Vapid02()
    vapid.generate_keys()
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    private = encode(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))
    public = encode(vapid.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
    values = {
        "ENGAGEMENT_EXTERNAL_ENABLED": "false",
        "ENGAGEMENT_EMAIL_ENABLED": "false",
        "ENGAGEMENT_PUSH_ENABLED": "false",
        "ENGAGEMENT_SMS_ENABLED": "false",
        "ENGAGEMENT_SIGNING_SECRET": secrets.token_urlsafe(48),
        "VAPID_PRIVATE_KEY": private,
        "VAPID_PUBLIC_KEY": public,
        "VAPID_SUBJECT": "https://neos.primusneo.com",
    }
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write("".join(f"{name}={value}\n" for name, value in values.items()))
    print("Created private notification configuration; all external channels remain disabled.")


if __name__ == "__main__":
    main()
