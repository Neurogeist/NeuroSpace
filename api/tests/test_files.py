import pytest
from fastapi import status
import io

def test_upload_file_success(client, test_session_id, test_file):
    """Test successful file upload."""
    files = {
        'file': ('test.txt', test_file, 'text/plain')
    }
    response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "file_id" in data
    assert "filename" in data
    assert data["filename"] == "test.txt"

def test_upload_file_invalid_type(client, test_session_id):
    """Test file upload with invalid file type."""
    # Create a file with invalid content
    invalid_file = io.BytesIO(b"Invalid content")
    files = {
        'file': ('test.exe', invalid_file, 'application/x-msdownload')
    }
    response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_upload_file_too_large(client, test_session_id):
    """Test file upload with file too large."""
    # Create a large file
    large_file = io.BytesIO(b"0" * (10 * 1024 * 1024 + 1))  # 10MB + 1 byte
    files = {
        'file': ('large.txt', large_file, 'text/plain')
    }
    response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

def test_list_files_success(client, test_session_id, mock_ipfs_service):
    """Test successful file listing."""
    response = client.get(f"/files/{test_session_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    for file in data:
        assert "file_id" in file
        assert "filename" in file
        assert "uploaded_at" in file

def test_get_file_success(client, test_session_id, mock_ipfs_service):
    """Test successful file retrieval."""
    # First upload a file
    test_file = io.BytesIO(b"Test content")
    files = {
        'file': ('test.txt', test_file, 'text/plain')
    }
    upload_response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    file_id = upload_response.json()["file_id"]
    
    # Then retrieve it
    response = client.get(f"/files/{test_session_id}/{file_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/plain"
    assert response.headers["content-disposition"] == 'attachment; filename="test.txt"'

def test_get_file_not_found(client, test_session_id):
    """Test file retrieval with non-existent file."""
    non_existent_file = "non-existent-file"
    response = client.get(f"/files/{test_session_id}/{non_existent_file}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_file_success(client, test_session_id, mock_ipfs_service):
    """Test successful file deletion."""
    # First upload a file
    test_file = io.BytesIO(b"Test content")
    files = {
        'file': ('test.txt', test_file, 'text/plain')
    }
    upload_response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    file_id = upload_response.json()["file_id"]
    
    # Then delete it
    response = client.delete(f"/files/{test_session_id}/{file_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_delete_file_not_found(client, test_session_id):
    """Test file deletion with non-existent file."""
    non_existent_file = "non-existent-file"
    response = client.delete(f"/files/{test_session_id}/{non_existent_file}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_rag_query_success(client, test_session_id, mock_rag_service):
    """Test successful RAG query."""
    query_data = {
        "query": "Test query",
        "model": "mixtral-8x7b-instruct",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    response = client.post(
        f"/rag/{test_session_id}/query",
        json=query_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "result" in data
    assert "sources" in data

def test_rag_query_no_files(client, test_session_id):
    """Test RAG query with no files uploaded."""
    query_data = {
        "query": "Test query",
        "model": "mixtral-8x7b-instruct",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    response = client.post(
        f"/rag/{test_session_id}/query",
        json=query_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_rag_query_invalid_model(client, test_session_id):
    """Test RAG query with invalid model."""
    query_data = {
        "query": "Test query",
        "model": "invalid-model",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    response = client.post(
        f"/rag/{test_session_id}/query",
        json=query_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_file_rate_limiting(client, test_session_id):
    """Test file upload rate limiting."""
    test_file = io.BytesIO(b"Test content")
    files = {
        'file': ('test.txt', test_file, 'text/plain')
    }
    
    # Upload multiple files in quick succession
    for _ in range(10):
        response = client.post(
            f"/files/{test_session_id}/upload",
            files=files
        )
    
    # The next upload should be rate limited
    response = client.post(
        f"/files/{test_session_id}/upload",
        files=files
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS 