import pytest
from unittest.mock import MagicMock, patch, mock_open
from atom.handlers.handler import S3Handler  # Replace `mymodule` with the actual module name

@pytest.fixture
def mock_s3_client():
    """Fixture for mocking the S3 client."""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def s3_handler(mock_s3_client):
    """Fixture for initializing S3Handler with a mocked S3 client."""
    return S3Handler(bucket_name="test-bucket", s3_client=mock_s3_client)

def test_initialization(s3_handler, mock_s3_client):
    """Test the initialization of S3Handler."""
    assert s3_handler.bucket_name == "test-bucket"
    assert s3_handler.s3_client == mock_s3_client
    assert s3_handler.custom_mime_types == {}

def test_put_success(s3_handler, mock_s3_client, tmp_path):
    """Test successful file upload."""
    # Temporary file
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("Sample data")

    mock_s3_client.s3_client.put_object.return_value = {}

    result = s3_handler.put(str(temp_file), "test-folder", public=True)

    assert result == "test-folder/test.txt"
    mock_s3_client.s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="test-folder/test.txt",
        Body=b"Sample data",
        ContentType="text/plain",
        ACL="public-read",
    )

def test_put_file_not_found(s3_handler):
    """Test upload with a nonexistent file."""
    result = s3_handler.put("nonexistent_file.txt", "test-folder")
    assert result is False

def test_put_exception(s3_handler, mock_s3_client, tmp_path):
    """Test upload when an exception is raised."""
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("Sample data")

    mock_s3_client.s3_client.put_object.side_effect = Exception("Upload error")

    result = s3_handler.put(str(temp_file), "test-folder")
    assert result is False

def test_get_success(s3_handler, mock_s3_client, tmp_path):
    """Test successful file download."""
    local_file = tmp_path / "downloaded.txt"

    with patch("builtins.open", mock_open()) as mocked_open:
        mock_s3_client.s3_client.download_fileobj.return_value = None
        result = s3_handler.get("test-folder/test.txt", str(local_file))

    assert result is True
    mock_s3_client.s3_client.download_fileobj.assert_called_once_with(
        "test-bucket", "test-folder/test.txt", mocked_open.return_value
    )

def test_get_no_such_key(s3_handler, mock_s3_client):
    """Test download with a nonexistent key."""
    mock_s3_client.s3_client.exceptions = MagicMock()
    mock_s3_client.s3_client.exceptions.NoSuchKey = FileNotFoundError

    # NoSuchKey exception
    mock_s3_client.s3_client.download_fileobj.side_effect = mock_s3_client.s3_client.exceptions.NoSuchKey("No such key")

    result = s3_handler.get("nonexistent-key", "local-path.txt")
    assert result is False