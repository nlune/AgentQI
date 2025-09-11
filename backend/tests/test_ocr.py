import os
import sys
import pymupdf
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_ocr import OCRDocProcessor
from utils.chunking import split_into_chunks
from settings import settings


def test_ocr_extraction():
    pass