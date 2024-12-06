# Implementation of the epistula protocol
Official documentation for the epistula protocol can be found [here](https://epistula.sybil.com/).

## What is epistula?
Epistula is a way to send public messages un a cryptographic way. It uses ed25519 signatures to sign messages and verify them. It also uses timestamps to prevent replay attacks. Epistula can be used for any protocol that uses ed25519 signatures and requires secure message passing.

## Why use epistula?
Epistula is a simple way to send messages between two parties. It is secure and easy to use. If you don't want to rely on outside services such as the `bittensor-sdk` to send messages, epistula is a good alternative.

## Quick Start

```python
from atom.epistula.epistula import Epistula
from substrateinterface import Keypair

# Initialize
epistula = Epistula()  # Default 8000ms timeout
# or 
epistula = Epistula(allowed_delta_ms=10000)  # Custom timeout

# Create message
message = {"data": "Hello"}
body = epistula.create_message_body(message)

# Generate headers
sender = Keypair.create_from_uri('//Alice')
headers = epistula.generate_header(
    hotkey=sender,
    body=body
)

# Verify signature
result = epistula.verify_signature(
    signature=headers["Epistula-Request-Signature"],
    body=body,
    timestamp=headers["Epistula-Timestamp"],
    uuid=headers["Epistula-Uuid"],
    signed_by=headers["Epistula-Signed-By"]
)

if result is None:
    print("Verified!")
else:
    print(f"Error: {result}")
```

## With Receiver (Optional)

```python
receiver = Keypair.create_from_uri('//Bob')
headers = epistula.generate_header(
    hotkey=sender,
    body=body,
    signed_for=receiver.ss58_address
)
```

## Headers Generated

- `Epistula-Version`
- `Epistula-Timestamp`
- `Epistula-Uuid`
- `Epistula-Signed-By`
- `Epistula-Request-Signature`
- `Epistula-Signed-For` (when receiver specified)
- `Epistula-Secret-Signature-[0-2]` (when receiver specified)

## Features

- Message signing with SubstrateInterface keypairs
- Timestamp-based validation
- UUID generation
- Optional receiver signing
- Automatic message body hashing
- Replay attack prevention

## Tests

```bash
pytest tests/test_epistula.py -v
```