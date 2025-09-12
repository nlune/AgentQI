#!/usr/bin/env python3
"""
Test script for the API endpoints.
Usage: Start the FastAPI server first with: python main.py
Then run this script to test the endpoints.
"""

import requests
import json
import os

API_BASE = "http://localhost:8000/api/v1"
TEST_DOC = "Certificate-BAM-A001.pdf"

def test_pdf_upload():
    """Test PDF upload and processing endpoint."""
    test_pdf = f"/home/lwei/Documents/AgentQI/test_files/{TEST_DOC}"
    
    if not os.path.exists(test_pdf):
        print(f"Test file not found: {test_pdf}")
        return False
    
    print("Testing PDF upload endpoint...")
    
    with open(test_pdf, 'rb') as f:
        files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
        response = requests.post(f"{API_BASE}/process-pdf", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Upload successful")
        print(f"  - Filename: {result.get('filename')}")
        print(f"  - Text length: {result.get('text_length')}")
        print(f"  - Line boxes: {result.get('line_boxes_count')}")
        return True
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return False

def test_query_endpoint():
    """Test the query endpoint."""
    print("\nTesting query endpoint...")
    
    queries = [
        "What type of certificate is this?",
        "What are the test parameters?",
        "Who issued this certificate?"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        
        try:
            resp = requests.post(
                f"{API_BASE}/query",
                params={"query": q, "doc_name": TEST_DOC, "k": 5}
            )
            
            if resp.status_code != 200:
                print(f"✗ Query failed: {resp.status_code}")
                print(f"  Error: {resp.text}")
                continue
            
            data = resp.json()
            print("✓ Query successful")
            print(f"  - Result: {data.get('result', '')[:120]}...")
            
            ev = data.get('evidence', {})
            print(f"  - Evidence doc_names: {ev.get('doc_name', [])}")
            print(f"  - Evidence chunk_ids: {ev.get('chunk_id', [])}")
            print(f"  - Context chunk count: {data.get('context_chunk_count')}\n")
        
        except requests.exceptions.ConnectionError:
            print("✗ Connection failed - is the server running?")
            return False
    
    return True

def main():
    print("=== AgentQI API Test ===\n")
    
    if test_pdf_upload():
        test_query_endpoint()
    
    print("\n=== API Test Complete ===")

if __name__ == "__main__":
    main()
