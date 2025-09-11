import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def test_process_pdf_endpoint():
    """Test the PDF OCR endpoint with a real PDF file."""
    
    # Path to test PDF file
    test_pdf_path = "../test_files/Certificate-BAM-A001.pdf"
    
    # Check if test file exists
    assert os.path.exists(test_pdf_path), f"Test file not found: {test_pdf_path}"
    
    # Open and send the PDF file
    with open(test_pdf_path, "rb") as pdf_file:
        response = client.post(
            "/api/v1/process-pdf",
            files={"file": ("Certificate-BAM-A001.pdf", pdf_file, "application/pdf")}
        )
    
    # Check response status
    assert response.status_code == 200
    
    # Check response content
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "Certificate-BAM-A001.pdf"
    assert "extracted_text" in data
    assert len(data["extracted_text"]) > 0
    assert "text_length" in data
    assert "document_name" in data
    assert data["document_name"] == "Certificate-BAM-A001.pdf"
    
    print(f"Extracted text length: {data['text_length']}")
    print(f"First 200 characters: {data['extracted_text'][:200]}")

def test_process_pdf_invalid_file():
    """Test the endpoint with a non-PDF file."""
    
    # Create a dummy text file
    response = client.post(
        "/api/v1/process-pdf",
        files={"file": ("test.txt", b"This is not a PDF", "text/plain")}
    )
    
    # Should return 400 error
    assert response.status_code == 400
    data = response.json()
    assert "Only PDF files are allowed" in data["detail"]

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

if __name__ == "__main__":
    # Run individual tests for debugging
    test_root_endpoint()
    test_process_pdf_invalid_file()
    test_process_pdf_endpoint()
    print("All tests passed!")
