import pytest
from substrateinterface import Keypair
from atom.epistula.epistula import Epistula

class TestEpistula:
    @pytest.fixture
    def epistula(self):
        return Epistula()

    @pytest.fixture
    def custom_delta_epistula(self):
        return Epistula(allowed_delta_ms=5000)

    @pytest.fixture
    def keypair(self):
        # Create a real keypair for testing
        return Keypair.create_from_mnemonic(Keypair.generate_mnemonic())
    
    @pytest.fixture
    def receiver_keypair(self):
        return Keypair.create_from_mnemonic(Keypair.generate_mnemonic())

    def test_initialization(self):
        # Test default initialization
        epistula = Epistula()
        assert epistula.ALLOWED_DELTA_MS == 8000
        assert epistula.VERSION == "2"

        # Test custom delta initialization
        custom_epistula = Epistula(allowed_delta_ms=5000)
        assert custom_epistula.ALLOWED_DELTA_MS == 5000

    def test_create_message_body(self, epistula):
        data = {"test": "value"}
        body = epistula.create_message_body(data)
        assert isinstance(body, bytes)
        assert body == b'{"test": "value"}'

    def test_generate_header_basic(self, epistula, keypair):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body)

        # Check required headers exist
        assert "Epistula-Version" in headers
        assert "Epistula-Timestamp" in headers
        assert "Epistula-Uuid" in headers
        assert "Epistula-Signed-By" in headers
        assert "Epistula-Request-Signature" in headers

        # Check header values
        assert headers["Epistula-Version"] == "2"
        assert headers["Epistula-Signed-By"] == keypair.ss58_address
        assert headers["Epistula-Request-Signature"].startswith("0x")

    def test_generate_header_with_signed_for(self, epistula, keypair, receiver_keypair):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body, signed_for=receiver_keypair.ss58_address)

        # Check additional headers exist
        assert "Epistula-Signed-For" in headers
        assert "Epistula-Secret-Signature-0" in headers
        assert "Epistula-Secret-Signature-1" in headers
        assert "Epistula-Secret-Signature-2" in headers

        assert headers["Epistula-Signed-For"] == receiver_keypair.ss58_address

    def test_verify_signature_valid(self, epistula, keypair):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body)
        
        result = epistula.verify_signature(
            headers["Epistula-Request-Signature"],
            body,
            headers["Epistula-Timestamp"],
            headers["Epistula-Uuid"],
            headers["Epistula-Signed-By"]
        )
        
        assert result is None  # None indicates successful verification

    def test_verify_signature_with_signed_for(self, epistula, keypair, receiver_keypair):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body, signed_for=receiver_keypair.ss58_address)
        
        result = epistula.verify_signature(
            headers["Epistula-Request-Signature"],
            body,
            headers["Epistula-Timestamp"],
            headers["Epistula-Uuid"],
            headers["Epistula-Signed-By"],
            signed_for=headers["Epistula-Signed-For"]
        )
        
        assert result is None

    def test_verify_signature_stale_request(self, epistula, keypair):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body)
        
        # Set current time to be well past the allowed delta
        current_time = int(headers["Epistula-Timestamp"]) + 10000
        
        result = epistula.verify_signature(
            headers["Epistula-Request-Signature"],
            body,
            headers["Epistula-Timestamp"],
            headers["Epistula-Uuid"],
            headers["Epistula-Signed-By"],
            now=current_time
        )
        
        assert result == "Request is too stale"

    @pytest.mark.parametrize("invalid_input,expected_error", [
        ({"signature": 123}, "Invalid signature type"),
        ({"signed_by": None}, "Invalid sender key type"),
        ({"uuid": 123}, "Invalid UUID type"),
        ({"body": "not-bytes"}, "Body is not of type bytes"),
        ({"signed_for": 123}, "Invalid receiver key type"),
        ({"timestamp": "not-a-number"}, "Invalid Timestamp"),
    ])
    def test_verify_signature_invalid_inputs(self, epistula, keypair, invalid_input, expected_error):
        body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, body)
        
        # Prepare base valid arguments
        args = {
            "signature": headers["Epistula-Request-Signature"],
            "body": body,
            "timestamp": headers["Epistula-Timestamp"],
            "uuid": headers["Epistula-Uuid"],
            "signed_by": headers["Epistula-Signed-By"]
        }
        
        # Update with invalid input
        args.update(invalid_input)
        
        result = epistula.verify_signature(**args)
        assert result == expected_error

    def test_verify_signature_tampered_body(self, epistula, keypair):
        original_body = epistula.create_message_body({"test": "value"})
        headers = epistula.generate_header(keypair, original_body)
        
        # Tamper with the body
        tampered_body = epistula.create_message_body({"test": "tampered"})
        
        result = epistula.verify_signature(
            headers["Epistula-Request-Signature"],
            tampered_body,
            headers["Epistula-Timestamp"],
            headers["Epistula-Uuid"],
            headers["Epistula-Signed-By"]
        )
        
        assert result == "Signature Mismatch"