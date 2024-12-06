import time
import json
from math import ceil
from uuid import uuid4
from hashlib import sha256
from typing import Dict, Any, Optional, Annotated

from substrateinterface import Keypair

class Epistula:
    """
    Manages the generation and verification of cryptographic signatures for messages.
    Handles both header generation and signature verification in a unified interface.
    """

    VERSION = "2"

    def __init__(self, allowed_delta_ms: Optional[int] = None):
        self.ALLOWED_DELTA_MS = 8000
        if allowed_delta_ms is not None:
            self.ALLOWED_DELTA_MS = allowed_delta_ms

    def generate_header(
        self,
        hotkey: Keypair,
        body: bytes,
        signed_for: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate headers containing signatures and metadata for a message.

        Args:
            hotkey: The keypair used for signing
            body: The message body in bytes
            signed_for: Optional receiver's address

        Returns:
            Dictionary containing all necessary headers
        """
        timestamp = round(time.time() * 1000)
        timestampInterval = ceil(timestamp / 1e4) * 1e4
        uuid = str(uuid4())

        # Create message for signing with optional signed_for
        message = f"{sha256(body).hexdigest()}.{uuid}.{timestamp}.{signed_for or ''}"

        headers = {
            "Epistula-Version": self.VERSION,
            "Epistula-Timestamp": str(timestamp),
            "Epistula-Uuid": uuid,
            "Epistula-Signed-By": hotkey.ss58_address,
            "Epistula-Request-Signature": "0x" + hotkey.sign(message).hex(),
        }

        # Only add signed_for related headers if it's specified
        if signed_for:
            headers["Epistula-Signed-For"] = signed_for
            # Generate time-based signatures for the interval
            for i, interval_offset in enumerate([-1, 0, 1]):
                signature = (
                    "0x"
                    + hotkey.sign(
                        f"{timestampInterval + interval_offset}.{signed_for}"
                    ).hex()
                )
                headers[f"Epistula-Secret-Signature-{i}"] = signature

        return headers

    def verify_signature(
        self,
        signature: str,
        body: bytes,
        timestamp: str,
        uuid: str,
        signed_by: str,
        signed_for: Optional[str] = None,
        now: Optional[int] = None,
    ) -> Optional[Annotated[str, "Error Message"]]:
        """
        Verify the signature of a message.

        Args:
            signature: The signature to verify
            body: Message body in bytes
            timestamp: Message timestamp
            uuid: Message UUID
            signed_by: Sender's address
            signed_for: Optional receiver's address
            now: Current timestamp (defaults to current time if not provided)

        Returns:
            None if verification succeeds, error message string if it fails
        """
        # Input validation
        if not isinstance(signature, str):
            return "Invalid signature type"
        if not isinstance(signed_by, str):
            return "Invalid sender key type"
        if not isinstance(uuid, str):
            return "Invalid UUID type"
        if not isinstance(body, bytes):
            return "Body is not of type bytes"
        if signed_for is not None and not isinstance(signed_for, str):
            return "Invalid receiver key type"

        try:
            timestamp = int(timestamp)
        except ValueError:
            return "Invalid Timestamp"

        # Time validation
        now = now if now is not None else round(time.time() * 1000)
        if timestamp + self.ALLOWED_DELTA_MS < now:
            return "Request is too stale"

        # Signature verification
        try:
            keypair = Keypair(ss58_address=signed_by)
            message = (
                f"{sha256(body).hexdigest()}.{uuid}.{timestamp}.{signed_for or ''}"
            )
            if not keypair.verify(message, signature):
                return "Signature Mismatch"
        except Exception as e:
            return f"Verification error: {str(e)}"

        return None

    @staticmethod
    def create_message_body(data: Dict) -> bytes:
        """Utility method to create message body from dictionary data"""
        return json.dumps(data).encode("utf-8")
