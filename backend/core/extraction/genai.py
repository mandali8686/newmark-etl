import os
import re
import json
import logging
import base64
from typing import Any, Dict, List, Optional, Union

import fitz  
from openai import OpenAI
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

def _page_png_b64(path: str, page_idx: int, dpi: int = 220) -> str:
    doc = fitz.open(path)
    pix = doc[page_idx].get_pixmap(dpi=dpi)
    bts = bytes(pix.tobytes("png"))
    return "data:image/png;base64," + base64.b64encode(bts).decode("ascii")

def call_openai_vision_on_pdf(path: str, max_pages: int = 3) -> Dict[str, Any]:
    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  

    doc = fitz.open(path)
    pages = min(max_pages, len(doc))

    content: List[Dict[str, Any]] = [{
        "type": "text",
        "text": (
            "Extract STRICT JSON with keys: property, units, sections, doc_type. "
            "Use numbers for sqft/rent, dates as YYYY-MM-DD. If labels appear, map them. "
            "If it's a lease/flyer/rent_roll, set doc_type accordingly. "
            "Return ONLY valid JSON, no comments or markdown fences."
        )
    }]
    for i in range(pages):
        content.append({
            "type": "image_url",
            "image_url": {"url": _page_png_b64(path, i)}
        })

    chat = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a precise information extractor."},
            {"role": "user", "content": content},
        ],
    )
    return json.loads(chat.choices[0].message.content)

def _truncate(s: str, max_chars: int = 120_000) -> str:
    s = s or ""
    return s[:max_chars]

def _extract_json(s: str) -> Dict[str, Any]:
    s = (s or "").strip()
    
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I).rstrip("` \n\t")
    
    m = re.search(r"\{.*\}\s*$", s, flags=re.S)
    s = m.group(0) if m else s
    return json.loads(s)

def _to_int(val: Any) -> Optional[int]:
    if val in (None, "", [], {}):
        return None
    try:
        if isinstance(val, (int, float)):
            return int(val)
        s = str(val).replace(",", "").strip()
        return int(float(s))
    except Exception:
        return None

def _to_float(val: Any) -> Optional[float]:
    if val in (None, "", [], {}):
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        s = (
            str(val)
            .replace(",", "")
            .replace("$", "")
            .replace("%", "")
            .strip()
        )
        return float(s)
    except Exception:
        return None

def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}

def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []

SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "property": {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]},
                "address": {"type": ["string", "null"]},
                "city": {"type": ["string", "null"]},
                "state": {"type": ["string", "null"]},
                "zipcode": {"type": ["string", "null"]},
                "year_built": {"type": ["string", "null"]},
                "sqft": {"type": ["string", "number", "null"]},
                "unit_count": {"type": ["string", "number", "null"]},
                "cap_rate": {"type": ["string", "number", "null"]},
            },
            "additionalProperties": False,
        },
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "unit_number": {"type": ["string", "null"]},
                    "unit_type": {"type": ["string", "null"]},
                    "beds": {"type": ["string", "null"]},
                    "baths": {"type": ["string", "null"]},
                    "sqft": {"type": ["string", "number", "null"]},
                    "rent": {"type": ["string", "number", "null"]},
                    "status": {"type": ["string", "null"]},
                    "lease_start": {"type": ["string", "null"]},
                    "lease_end": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "text": {"type": ["string", "null"]},
                    "page": {"type": ["integer", "null"]},
                    "bbox": {"type": "array", "items": {"type": "number"}},
                },
                "additionalProperties": True,
            },
        },
        "doc_type": {"type": ["string", "null"]},
    },
    "required": ["property", "units", "sections"],
}

def call_openai_structured(doc_text: str) -> Dict[str, Any]:
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI()

    system = (
        "You extract structured real estate data from the file. Read the pdf file carefully."
        "You may need to read both the text and images to get as much information as possible, use the common sense to understand the file and get the related information. "
        "Return STRICT JSON with these keys exactly and no extras: "
        "{property:{name,address,city,state,zipcode,year_built,sqft,unit_count,cap_rate},"
        "units:[{unit_number,unit_type,beds,baths,sqft,rent,status,lease_start,lease_end}],"
        "sections:[{title,text,page,bbox}],doc_type}. "
        "If values are numeric (sqft, unit_count, cap_rate, rent), output numbers (not strings) when obvious. "
        "Dates may stay as strings. No commentary. No markdown fences."
    )
    user = (
        "Document text:\n```\n"
        + _truncate(doc_text)
        + "\n```\nRespond ONLY with a JSON object."
    )

    chat = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = chat.choices[0].message.content
    logger.info("GEN AI Response: %s",content)
    try:
        return _extract_json(content)
    except Exception as e:
        logger.exception("Failed to parse OpenAI JSON: %s; raw content: %r", e, content[:5000])
        raise

def call_langchain_structured(doc_text: str) -> Dict[str, Any]:

    class Unit(BaseModel):
        unit_number: Optional[str] = None
        unit_type: Optional[str] = None
        beds: Optional[str] = None
        baths: Optional[str] = None
        sqft: Optional[Union[str, float, int]] = None
        rent: Optional[Union[str, float, int]] = None
        status: Optional[str] = None
        lease_start: Optional[str] = None
        lease_end: Optional[str] = None

    class PropertyModel(BaseModel):
        name: Optional[str] = None
        address: Optional[str] = None
        city: Optional[str] = None
        state: Optional[str] = None
        zipcode: Optional[str] = None
        year_built: Optional[str] = None
        sqft: Optional[Union[str, float, int]] = None
        unit_count: Optional[Union[str, float, int]] = None
        cap_rate: Optional[Union[str, float, int]] = None

    class ExtractOut(BaseModel):
        property: PropertyModel
        units: List[Unit] = Field(default_factory=list)
        sections: List[dict] = Field(default_factory=list)
        doc_type: Optional[str] = None

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)
    structured_llm = llm.with_structured_output(ExtractOut)
    out: ExtractOut = structured_llm.invoke([
        ("system",
         "You extract structured real estate data from text (flyers, rent rolls, leases). "
         "Return data that maps to the provided Pydantic schema exactly, with no extra fields."),
        ("user", _truncate(doc_text)),
    ])
    return json.loads(out.model_dump_json())

PROPERTY_ALLOWED = {
    "name", "address", "city", "state", "zipcode", "year_built", "sqft", "unit_count", "cap_rate"
}
UNIT_ALLOWED = {
    "unit_number", "unit_type", "beds", "baths", "sqft", "rent", "status", "lease_start", "lease_end"
}

def normalize_to_model_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drop unknown keys and coerce numeric-like fields to proper numeric types,
    so your Django models accept them without errors.
    This also guarantees: property is dict, units is list, sections is list.
    """
    if isinstance(data, str):
        try:
            data = _extract_json(data)
        except Exception:
            logger.warning("normalize_to_model_schema: received string that is not JSON; dropping to empty.")
            data = {}

    data = _as_dict(data)
    out: Dict[str, Any] = {
        "property": {},
        "units": [],
        "sections": _as_list(data.get("sections")),
        "doc_type": data.get("doc_type"),
    }

    prop_in = _as_dict(data.get("property"))
    for k in PROPERTY_ALLOWED:
        v = prop_in.get(k)
        if k in {"sqft", "unit_count"}:
            out["property"][k] = _to_int(v)
        elif k == "cap_rate":
            out["property"][k] = _to_float(v)
        else:
            out["property"][k] = v if v is not None else ""

    units_in = _as_list(data.get("units"))
    norm_units: List[Dict[str, Any]] = []
    for u in units_in:
        u = _as_dict(u)
        norm: Dict[str, Any] = {}
        for k in UNIT_ALLOWED:
            v = u.get(k)
            if k == "sqft":
                norm[k] = _to_int(v)
            elif k == "rent":
                norm[k] = _to_float(v)
            else:
                norm[k] = v if v is not None else ""
        
        if any(val not in (None, "", [], {}) for val in norm.values()):
            norm_units.append(norm)
    out["units"] = norm_units

    
    return out

def genai_enrich(result: Dict[str, Any], fulltext: str, *, pdf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Enrich parser result with LLM output (if GENAI_PROVIDER is set).
      - GENAI_PROVIDER=openai        -> text-only JSON mode
      - GENAI_PROVIDER=openai_vision -> first N pages as images
      - GENAI_PROVIDER=lc|langchain  -> LangChain structured
    We always normalize LLM output to model schema BEFORE merging to avoid
    'str' object has no attribute 'items' and similar type errors.
    """
    provider = os.getenv("GENAI_PROVIDER")
    if not provider:
        return result

    try:
        
        if provider.lower() == "openai":
            raw = call_openai_structured(fulltext)
        elif provider.lower() == "openai_vision" and pdf_path:
            raw = call_openai_vision_on_pdf(pdf_path, max_pages=int(os.getenv("VISION_MAX_PAGES", "3")))
        elif provider.lower() in {"lc", "langchain"}:
            raw = call_langchain_structured(fulltext)
        else:
            return result

        llm_out = normalize_to_model_schema(raw)

        merged = dict(result)
        merged.setdefault("property", {})

        for k, v in llm_out.get("property", {}).items():
            if merged["property"].get(k) in (None, "", [], {}):
                if v not in (None, "", [], {}):
                    merged["property"][k] = v

        if not merged.get("units") and llm_out.get("units"):
            merged["units"] = llm_out["units"]
        if not merged.get("sections") and llm_out.get("sections"):
            merged["sections"] = llm_out["sections"]
        if not merged.get("doc_type") and llm_out.get("doc_type"):
            merged["doc_type"] = llm_out["doc_type"]

        return merged

    except Exception as e:
        logger.exception("genai_enrich failed: %s", e)
        return result


__all__ = ["genai_enrich", "call_openai_structured", "call_langchain_structured", "SCHEMA"]
