import fitz
import pdfplumber
from .tables import extract_tables
from .utils import find_value_near, sections_from_layout
from .ocr import get_page_words_with_ocr_fallback, get_fulltext_with_ocr_fallback

LABELS = {
    "Property Name": ["name"],
    "Address": ["address"],
    "Units": ["unit_count"],
    "Year Built": ["year_built"],
    "SF": ["sqft"],
    "Cap Rate": ["cap_rate"],
}

def parse_flyer(path: str):
    doc = fitz.open(path)
    fulltext = get_fulltext_with_ocr_fallback(path, dpi=300)
    sections = sections_from_layout(path) or []
    property_fields = {}
    citations = []

    for p in range(min(2, len(doc))):
        words = get_page_words_with_ocr_fallback(doc, path, p, dpi=300)
        for label in LABELS:
            hit = find_value_near(words, label)
            if hit:
                key = LABELS[label][0]
                property_fields[key] = hit["value"]
                citations.append({
                    "field": key,
                    "page": p,
                    "bbox": hit["bbox"],
                    "snippet": hit["value"],
                })

    return {
        "property": property_fields,
        "units": [],
        "sections": sections,
        "citations": citations,
        "fulltext_hint": fulltext[:5000], 
    }

def parse_rent_roll(path: str):
    tables = extract_tables(path)
    units = []
    citations = []
    headers_map = {
        "unit": "unit_number",
        "beds": "beds",
        "baths": "baths",
        "rent": "rent",
        "sqft": "sqft",
        "status": "status",
        "lease start": "lease_start",
        "lease end": "lease_end",
    }
    for t in tables:
        df = t.df
        header = [str(h).strip().lower() for h in list(df.iloc[0])]
        col_idx = {}
        for i, h in enumerate(header):
            for k, v in headers_map.items():
                if k in h:
                    col_idx[v] = i
        for ridx in range(1, len(df)):
            row = df.iloc[ridx]
            record = {}
            for k, i in col_idx.items():
                record[k] = str(row[i]).strip()
            if any(record.values()):
                units.append(record)
    return {"property": {}, "units": units, "sections": [], "citations": citations}
