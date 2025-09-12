#!/usr/bin/env python3
"""Single-query API test with highlight generation."""
import requests, os

API_BASE = "http://localhost:8000/api/v1"
TEST_DOC = "Certificate-BAM-A001.pdf"
SINGLE_QUERY = "What type of certificate is this?"


def test_pdf_upload():
    pdf_path = f"/home/lwei/Documents/AgentQI/test_files/{TEST_DOC}"
    if not os.path.exists(pdf_path):
        print("Missing test PDF:", pdf_path)
        return None
    print("Uploading PDF ...")
    with open(pdf_path, 'rb') as f:
        resp = requests.post(f"{API_BASE}/process-pdf", files={'file': (TEST_DOC, f, 'application/pdf')})
    if resp.status_code != 200:
        print("Upload failed", resp.status_code, resp.text)
        return None
    print("Upload OK")
    return resp.json()


def run_single_query():
    print("\nRunning query ...")
    resp = requests.post(f"{API_BASE}/query", params={"query": SINGLE_QUERY, "doc_name": TEST_DOC, "k": 5})
    if resp.status_code != 200:
        print("Query failed", resp.status_code, resp.text)
        return None
    data = resp.json()
    ev = data.get('evidence', {})
    chunk_ids = ev.get('chunk_id', []) or []
    print("Query OK. Chunk IDs:", chunk_ids)
    return data, chunk_ids


def highlight(chunk_ids):
    if not chunk_ids:
        chunk_ids = [0]
    payload = {"doc_name": TEST_DOC, "chunk_ids": chunk_ids[:3], "color": [1, 0.85, 0.2], "return_pdf": False}
    print("\nCalling highlight with:", payload)
    url = f"{API_BASE}/highlight"
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print("Highlight 404? Ensure server restarted after adding endpoint.")
        print("Status:", resp.status_code, "Body:", resp.text)
        print("Debug: Trying health check /docs ->", requests.get("http://localhost:8000/docs").status_code)
        return None
    data = resp.json()
    print("Highlight OK ->", data.get('annotated_pdf_url'))
    return data


def main():
    if not test_pdf_upload():
        return
    qr = run_single_query()
    print("\nQuery Result:", qr)
    if not qr:
        return
    _, chunk_ids = qr
    highlight(chunk_ids)
    print("\nDone")


if __name__ == "__main__":
    main()
