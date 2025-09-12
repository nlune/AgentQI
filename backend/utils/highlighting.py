"""Reusable PDF highlight generation utilities.

This module centralizes the logic for turning a list of chunk_ids
into an annotated PDF with semi–transparent rectangle annotations.

Public function:
    generate_highlight_pdf(doc_name: str, chunk_ids: List[int], color: Optional[List[float]] = None) -> dict

Returns a dict with keys:
    success, doc_name, chunk_ids, annotated_pdf, annotated_pdf_path,
    annotated_pdf_url (relative), highlights (list of {chunk_id,page,bbox,header}), cached (bool)
"""
from __future__ import annotations
import os
import hashlib
import ast
from typing import List, Optional
import pymupdf
from core.vec_db import VecDB
from settings import settings  # fixed import (was from . import settings)

import code

# Storage directories (kept consistent with endpoint definitions)
ORIGINAL_DIR = os.path.join("storage", "original_pdfs")
ANNOTATED_DIR = os.path.join("storage", "annotated_pdfs")
os.makedirs(ORIGINAL_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)


def _fetch_chunk_metadata(doc_name: str, chunk_ids: List[int]) -> List[dict]:
    """Fetch metadata for given chunk indices using direct ID lookup."""
    if not chunk_ids:
        return []
    vec_db = VecDB(settings=settings) # Use centralized path from settings
    
    # Construct the specific IDs to fetch
    id_names = [f"{doc_name}_{cid}" for cid in chunk_ids]
    
    try:
        # Retrieve by specific IDs
        results = vec_db.collection.get(ids=id_names, include=["metadatas"])
    except Exception:
        return []
        
    metadatas = results.get("metadatas", [])
    
    # Filter out any potential nulls if some IDs were not found
    return [m for m in metadatas if m]


def _prepare_highlights(metadatas: List[dict]) -> List[dict]:
    highlights = []
    for md in metadatas:
        chunk_idx = md.get("chunk_idx")
        page = md.get("page")
        raw_bbox = md.get("bbox", "[]")
        invalid = False
        if isinstance(raw_bbox, str):
            try:
                bbox = ast.literal_eval(raw_bbox)
            except Exception:
                bbox = []
                invalid = True
        else:
            bbox = raw_bbox
        if bbox is None:
            invalid = True
            bbox = []
        if not bbox or len(bbox) < 4:
            # Tag invalid bbox so caller can debug (do not append highlight)
            md["_invalid_bbox"] = True
            continue
        highlights.append(
            {
                "chunk_id": chunk_idx,
                "page": page,
                "bbox": bbox,
                "header": md.get("header", ""),
            }
        )

    return highlights


def generate_highlight_pdf(
    doc_name: str, chunk_ids: List[int], color: Optional[List[float]] = None
) -> dict:
    """Create (or reuse cached) highlighted PDF for given chunks.

    Args:
        doc_name: Exact document name used at ingestion (filename).
        chunk_ids: List of integer chunk indices.
        color: Optional RGB list values 0-1.

    Returns:
        Dict with highlight metadata (see module docstring).
    """
    original_path = os.path.join(ORIGINAL_DIR, doc_name)
    if not os.path.exists(original_path):
        print(f"Original document not found: {original_path}")
        return {"success": False, "error": "Original document not found"}

    # de-duplicate & preserve deterministic ordering for cache key
    norm_ids = sorted(set(int(c) for c in chunk_ids))
    if not norm_ids:
        return {"success": False, "error": "No chunk IDs provided"}

    # Determine color early for cache key
    rgb = tuple(color[:3]) if color and len(color) >= 3 else (1, 0.85, 0.2)

    # Build a cache key based on doc, chunk set, and color so different
    # highlight requests produce distinct annotated files but can be reused
    key = f"{doc_name}|{','.join(map(str, norm_ids))}|{','.join(map(lambda x: f'{x:.3f}', rgb))}"
    key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()[:10]

    annotated_name = f"{doc_name}__annotated_{key_hash}.pdf"
    annotated_path = os.path.join(ANNOTATED_DIR, annotated_name)

    needs_render = not os.path.exists(annotated_path)

    metadatas = _fetch_chunk_metadata(doc_name, norm_ids)
    highlights = _prepare_highlights(metadatas)

    if not highlights:
        return {
            "success": False,
            "error": "No valid highlights found for the provided chunk_ids",
            "chunk_ids": norm_ids,
        }

    if needs_render:
        try:
            doc = pymupdf.open(original_path)
            for h in highlights:
                page_idx = h["page"]
                if page_idx is None or page_idx >= len(doc):
                    continue
                x0, y0, x1, y1 = h["bbox"][:4]
                rect = pymupdf.Rect(x0, y0, x1, y1)
                annot = doc[page_idx].add_rect_annot(rect)
                annot.set_colors(stroke=rgb, fill=rgb)
                annot.set_opacity(0.25)
                annot.update()
            doc.save(annotated_path)
            doc.close()
        except Exception as e:
            return {"success": False, "error": f"Failed rendering PDF: {e}"}

    rel_url = f"/pdfs/annotated/{annotated_name}"
    return {
        "success": True,
        "doc_name": doc_name,
        "chunk_ids": norm_ids,
        "annotated_pdf": annotated_name,
        "annotated_pdf_path": annotated_path,
        "annotated_pdf_url": rel_url,
        "highlights": highlights,
        "cached": not needs_render,
        "page": highlights[0]["page"] if highlights else None,
        "bbox": highlights[0]["bbox"] if highlights else None,
    }

__all__ = ["generate_highlight_pdf"]
