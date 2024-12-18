import time
import json
from math import ceil
from uuid import uuid4
from hashlib import sha256
from substrateinterface import Keypair
from typing import Dict, Any, Optional, Annotated

from .__init__ import EPISTULA_VERSION
from pydantic import BaseModel, Field, ValidationError

"""Cryptographic signature management module for secure message handling.

This module provides a robust framework for generating and verifying cryptographic
signatures for messages in a distributed system. It implements time-based validation,
UUID tracking, and optional recipient-specific signing.

Key Features:
    - Message signature generation and verification
    - Time-based signature validation with configurable time windows
    - Support for recipient-specific message signing
    - Comprehensive input validation using Pydantic
    - JSON message body handling
"""

class VerifySignatureRequest(BaseModel):
    """Validation model for signature verification requests.
    
    This Pydantic model enforces strict typing and format validation for all
    parameters required in the signature verification process.

    Attributes:
        body (bytes): The raw message body to verify
        timestamp (int): Unix timestamp in milliseconds when the message was signed
        signature (str): Hex-encoded signature with '0x' prefix, must be 64 characters
        uuid (str): Unique identifier for the message, must be valid UUID format
        signed_by (str): The SS58 address of the signing keypair
        signed_for (Optional[str]): The intended recipient's address, if any
        now (Optional[int]): Current timestamp for testing purposes
    """

class Epistula:
    """Cryptographic signature manager for secure message handling.

    This class provides a comprehensive interface for generating and verifying
    cryptographic signatures in a distributed messaging system. It supports
    time-based validation windows and recipient-specific signing.

    Attributes:
        ALLOWED_DELTA_MS (int): Maximum allowed time difference in milliseconds
            between message timestamp and verification time
    """

    def __init__(self, allowed_delta_ms: Optional[int] = None):
        self.ALLOWED_DELTA_MS = allowed_delta_ms if allowed_delta_ms is not None else 8000

    def generate_header(
        self,
        hotkey: Keypair,
        body: bytes,
        signed_for: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate cryptographic headers for a message.

        Creates a complete set of headers including signatures and metadata
        required for message verification. Optionally generates additional
        time-based signatures for recipient-specific messages.

        Args:
            hotkey: The keypair used for signing the message
            body: Raw message content in bytes
            signed_for: Optional recipient SS58 address for targeted messages

        Returns:
            Dictionary containing all required headers:
                - Epistula-Version: Protocol version
                - Epistula-Timestamp: Message timestamp
                - Epistula-Uuid: Unique message identifier
                - Epistula-Signed-By: Sender's SS58 address
                - Epistula-Request-Signature: Primary message signature
                - Epistula-Signed-For: (Optional) Recipient's address
                - Epistula-Secret-Signature-[0-2]: (Optional) Time-based signatures
        """
        timestamp = round(time.time() * 1000)
        timestampInterval = ceil(timestamp / 1e4) * 1e4
        uuid = str(uuid4())

        # Create message for signing with optional signed_for
        message = f"{sha256(body).hexdigest()}.{uuid}.{timestamp}.{signed_for or ''}"

        headers = {
            "Epistula-Version": EPISTULA_VERSION,
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
        """Verify the authenticity of a signed message.

        Performs comprehensive validation including:
            - Input format validation
            - Timestamp freshness check
            - Cryptographic signature verification
            - Optional recipient validation

        Args:
            signature: Hex-encoded signature with '0x' prefix
            body: Raw message content in bytes
            timestamp: Message timestamp in milliseconds
            uuid: Unique message identifier
            signed_by: Sender's SS58 address
            signed_for: Optional recipient's SS58 address
            now: Optional timestamp for testing purposes

        Returns:
            None if verification succeeds, or an error message string describing
            the reason for validation failure

        Note:
            The verification will fail if the message is too old (exceeds ALLOWED_DELTA_MS)
            or if any of the cryptographic checks fail
        """

        #Pydantic will enforce the validation typing rules
        try:
            VerifySignatureRequest(
                body=body,
                timestamp=timestamp,
                signature=signature,
                uuid=uuid,
                signed_by=signed_by,
                signed_for=signed_for,
                now=now,
            )

        except ValidationError as e:
            return f"Validation Error: {str(e)}"

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
        """Convert a dictionary into a deterministic JSON-encoded byte string.

        Creates a consistent byte representation of dictionary data for signing,
        ensuring that the same input always produces the same output bytes.

        Args:
            data: Dictionary containing message data

        Returns:
            UTF-8 encoded bytes of the sorted JSON string representation
        """
        return json.dumps(data, default=str, sort_keys=True).encode("utf-8")
