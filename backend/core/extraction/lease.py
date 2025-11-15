import re
import fitz  
import pdfplumber

def _first(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

def _num(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    if not m: return None
    s = m.group(1).replace(",", "").replace("$", "").strip()
    try:
        return float(s)
    except Exception:
        return s

def _find_bbox(doc, page_idx, needle):
    """Best-effort bbox for a label/value occurrence."""
    try:
        rects = doc[page_idx].search_for(needle, hit_max=1)
        if rects:
            r = rects[0]
            return [float(r.x0), float(r.y0), float(r.x1), float(r.y1)]
    except Exception:
        pass
    return None

def parse_lease(path: str):
    doc = fitz.open(path)
    with pdfplumber.open(path) as pdf:
        fulltext = "\n".join(p.extract_text() or "" for p in pdf.pages)

    property_fields = {
        "name": _first(r"Tenant:\s*([^\n]+)", fulltext),
        "address": _first(r"located at\s*(.+?)\s*\(\"Premises\"\)", fulltext),
        "sqft": _num(r"approximately\s*([\d,]+)\s*(?:rentable|RSF)", fulltext),
        "unit_count": None,  
        "cap_rate": None,    
        "lease_start": _first(r"commence(?:s|) on\s*([0-9/.-]+)", fulltext),
        "lease_end": _first(r"expire(?:s|) on\s*([0-9/.-]+)", fulltext),
        "base_rent_monthly": _num(r"base monthly rent of\s*\$?([\d,\.]+)", fulltext),
        "escalation": _first(r"increase by\s*([\d\.%]+)\s*annually", fulltext),
        "security_deposit": _first(r"Security Deposit:\s*(.+)|deposit an amount.*", fulltext),
        "use": _first(r"used.*for\s*([^.]+)\.", fulltext),
        "renewal": _first(r"renew.*?(five.*?year.*?|additional.*?term.*?)\.", fulltext),
        "landlord": _first(r"Landlord:\s*([^\n]+)", fulltext),
        "tenant": _first(r"Tenant:\s*([^\n]+)", fulltext),
        "date": _first(r"Date:\s*([^\n]+)", fulltext),
    }
    labels = {
        "base_rent_monthly": "Base Rent",
        "lease_start": "commence",
        "lease_end": "expire",
        "use": "used",
        "renewal": "renew",
        "landlord": "Landlord:",
        "tenant": "Tenant:",
        "address": "located at",
        "sqft": "rentable square feet",
        "date": "Date:",
    }
    citations = []
    for p in range(len(doc)):
        page_text = doc[p].get_text()
        for field, needle in list(labels.items()):
            if property_fields.get(field) and needle.lower() in page_text.lower():
                bbox = _find_bbox(doc, p, needle) or _find_bbox(doc, p, str(property_fields[field]).split()[0])
                if bbox:
                    citations.append({
                        "field": field,
                        "page": p,
                        "bbox": bbox,
                        "snippet": property_fields[field],
                    })

    return {
        "property": {k: v for k, v in property_fields.items() if v not in (None, "")},
        "units": [],
        "sections": [],      
        "citations": citations
    }
