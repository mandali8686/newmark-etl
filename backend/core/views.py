from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from .models import Document, Property, Unit, Section, FieldCitation
from .serializers import (
    DocumentSerializer,
    PropertySerializer,
    UnitSerializer,
    SectionSerializer,
    FieldCitationSerializer,
)
import json
import logging

from .extraction.pipeline import extract

logger = logging.getLogger(__name__)

def _coerce_int(v, default=None):
    if v is None or v == "":
        return default
    try:
        return int(float(v))  
    except Exception:
        return default

def _coerce_float(v, default=None):
    if v is None or v == "":
        return default
    try:
        return float(v)
    except Exception:
        return default

def _safe_bbox(bbox):
    """Return [x0,y0,x1,y1] of floats; fallback to zeros."""
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return [0.0, 0.0, 0.0, 0.0]
    try:
        return [float(b) for b in bbox]
    except Exception:
        return [0.0, 0.0, 0.0, 0.0]

def _persisted_doc_type(requested: str) -> str:
    """Map requested doc_type to one of Document's choices; default to flyer."""
    requested = (requested or "").lower()
    valid = {Document.RENT_ROLL, Document.FLYER}
    return requested if requested in valid else Document.FLYER

VALID_DOC_TYPES = {
    getattr(Document, "RENT_ROLL", "rent_roll"),
    getattr(Document, "FLYER", "flyer"),
    "lease",
    "auto",
}

import re

_num_re = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|[-+]?\d+(?:\.\d+)?")

def to_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    return str(v).strip()

def to_int(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int,)):
        return v
    s = str(v)
    m = _num_re.search(s)
    if not m:
        return None
    try:
        return int(float(m.group(0).replace(",", "")))
    except Exception:
        return None

def to_float(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v)
    m = _num_re.search(s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except Exception:
        return None

def as_plain_str(v) -> str:
    return "" if v is None else str(v).strip()


@method_decorator(csrf_exempt, name="dispatch")
class UploadView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        doc_type = (request.data.get("doc_type") or "auto").lower()
        if not file or doc_type not in VALID_DOC_TYPES:
            return Response(
                {"detail": f"file and valid doc_type required; one of {sorted(VALID_DOC_TYPES)}"},
                status=400,
            )

        d = Document.objects.create(
            file=file,
            doc_type=doc_type if doc_type != "auto" else getattr(Document, "FLYER", "flyer"),
        )
        d.pages = 0
        d.save()

        res = extract(d.file.path, doc_type)
        logger.info("EXTRACT RESULT (doc %s): %s", d.id, json.dumps(res, indent=2, default=str))
        if isinstance(res, dict) and res.get("doc_type"):
            d.doc_type = res["doc_type"]

        try:
            d.pages = len(fitz.open(d.file.path))
        except Exception:
            pass
        d.save()

        with transaction.atomic():
            prop = None
            p_in = res.get("property") or {}
            if p_in:
                pdata = {
                    "name": to_str(p_in.get("name")),
                    "address": to_str(p_in.get("address")),
                    "city": to_str(p_in.get("city")),
                    "state": to_str(p_in.get("state")),
                    "zipcode": as_plain_str(p_in.get("zipcode")),
                    "year_built": to_str(p_in.get("year_built")),  
                    "sqft": to_int(p_in.get("sqft")),
                    "unit_count": to_int(p_in.get("unit_count")),
                    "cap_rate": to_float(p_in.get("cap_rate")),
                }
                prop = Property.objects.create(**pdata, source_document=d)

            
            for u in res.get("units", []):
                if prop is None:
                    prop = Property.objects.create(source_document=d)
                Unit.objects.create(
                    property=prop,
                    unit_number=to_str(u.get("unit_number")),
                    beds=to_str(u.get("beds")),
                    baths=to_str(u.get("baths")),
                    sqft=to_int(u.get("sqft")),
                    rent=to_float(u.get("rent")),
                    status=to_str(u.get("status")),
                    lease_start=to_str(u.get("lease_start")),  
                    lease_end=to_str(u.get("lease_end")),
                )

            
            for s in res.get("sections", []):
                bbox = s.get("bbox") or [0, 0, 0, 0]
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    bbox = [0, 0, 0, 0]
                Section.objects.create(
                    document=d,
                    page=s.get("page", 0) or 0,
                    title=to_str(s.get("title")),
                    text=to_str(s.get("text")),
                    bbox_x0=float(bbox[0]),
                    bbox_y0=float(bbox[1]),
                    bbox_x1=float(bbox[2]),
                    bbox_y1=float(bbox[3]),
                )

            
            for c in res.get("citations", []):
                bbox = c.get("bbox") or [0, 0, 0, 0]
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    bbox = [0, 0, 0, 0]
                FieldCitation.objects.create(
                    document=d,
                    model_name="Property",
                    record_id=prop.id if prop else 0,
                    field_name=to_str(c.get("field")),
                    page=c.get("page", 0) or 0,
                    x0=float(bbox[0]),
                    y0=float(bbox[1]),
                    x1=float(bbox[2]),
                    y1=float(bbox[3]),
                    snippet=to_str(c.get("snippet")),
                )

        return Response({"document_id": d.id, "property_id": prop.id if prop else None}, status=201)


class DocumentDetail(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class PropertiesList(generics.ListAPIView):
    serializer_class = PropertySerializer
    def get_queryset(self):
        qs = Property.objects.all().order_by("id")

        
        src = self.request.query_params.get("source_document")
        if src:
            try:
                qs = qs.filter(source_document_id=int(src))
            except Exception:
                qs = qs.none()

        name = self.request.query_params.get("name")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        min_units = self.request.query_params.get("min_units")
        max_rent = self.request.query_params.get("max_rent")
        if name:
            qs = qs.filter(name__icontains=name)
        if city:
            qs = qs.filter(city__icontains=city)
        if state:
            qs = qs.filter(state__icontains=state)
        if min_units:
            try: qs = qs.filter(unit_count__gte=int(min_units))
            except: pass
        if max_rent:
            try: qs = qs.filter(units__rent__lte=float(max_rent)).distinct()
            except: pass
        return qs


class UnitsList(generics.ListAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):
        qs = Unit.objects.all().order_by("id")
        prop = self.request.query_params.get("property_id")
        beds = self.request.query_params.get("beds")
        if prop:
            try:
                qs = qs.filter(property_id=int(prop))
            except Exception:
                qs = qs.none()
        if beds:
            qs = qs.filter(beds__icontains=beds)
        return qs

class PropertyDetail(generics.RetrieveAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

class SearchView(APIView):
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        props = Property.objects.filter(name__icontains=q) | Property.objects.filter(address__icontains=q)
        units = Unit.objects.filter(unit_number__icontains=q) | Unit.objects.filter(status__icontains=q)
        return Response(
            {
                "properties": PropertySerializer(props[:50], many=True).data,
                "units": UnitSerializer(units[:100], many=True).data,
            }
        )

class CitationsView(APIView):
    def get(self, request, model_name: str, record_id: int):
        cites = FieldCitation.objects.filter(model_name=model_name, record_id=record_id)
        return Response(FieldCitationSerializer(cites, many=True).data)
