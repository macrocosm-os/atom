import pytest
from unittest.mock import patch
from atom.handlers.s3_client import S3Client


@patch("boto3.session.Session.client")
def test_s3_client_initialization(mock_boto_client):
    # Mock the return value of the boto3 client
    mock_s3 = mock_boto_client.return_value

    # Instantiate S3Client
    client = S3Client(
        region_name="mock-region",
        endpoint_url="http://mock-endpoint",
        access_key_id="mock-access-key",
        secret_access_key="mock-secret-key",
    )

    # Verify boto3 client is called with correct parameters
    mock_boto_client.assert_called_once_with(
        "s3",
        region_name="mock-region",
        endpoint_url="http://mock-endpoint",
        aws_access_key_id="mock-access-key",
        aws_secret_access_key="mock-secret-key",
    )
    assert client.s3_client == mock_s3
