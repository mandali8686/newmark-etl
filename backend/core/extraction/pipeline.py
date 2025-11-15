from .parsers import parse_flyer, parse_rent_roll
from .lease import parse_lease
from .genai import genai_enrich
import pdfplumber, fitz
from .ocr import get_fulltext_with_ocr_fallback

def extract(path: str, doc_type: str):
    if doc_type == "flyer":
        res = parse_flyer(path)
    elif doc_type == "rent_roll":
        res = parse_rent_roll(path)
    elif doc_type == "lease":
        res = parse_lease(path)
    else:
        head = (fitz.open(path)[0].get_text() or "").lower()
        res = parse_lease(path) if "lease" in head else parse_flyer(path)
    try:
        with pdfplumber.open(path) as pdf:
            fulltext = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        
        fulltext = get_fulltext_with_ocr_fallback(path, dpi=350)

    print("Loading Gen AI enrich")
    res = genai_enrich(res, fulltext, pdf_path=path)
    return res
