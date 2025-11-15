# Newmark ETL — Flyer/Rent-Roll/Lease Extraction Demo

A small full-stack app that:

* lets you **upload** a commercial real-estate PDF (flyer / rent-roll / lease),
* **extracts** structured data (property info, units, sections, citations) using OCR and/or an LLM,
* **stores** results in a Django/Postgres (or SQLite) backend,
* **previews** the PDF with highlights and shows the extracted fields in a React frontend.

---

## Table of Contents

* [Architecture](#architecture)
* [Backend (Django/DRF)](#backend-djangodrf)

  * [Environment variables](#environment-variables-backend)
  * [Setup & Run](#setup--run-backend)
  * [API Routes](#api-routes)
  * [Data Models](#data-models)
  * [Extraction Pipeline](#extraction-pipeline)
* [Frontend (React/Vite)](#frontend-reactvite)

  * [Environment variables](#environment-variables-frontend)
  * [Setup & Run](#setup--run-frontend)
  * [Key Components](#key-components)
* [Typical Workflow](#typical-workflow)
* [Troubleshooting](#troubleshooting)
* [Extending](#extending)

---

## Architecture

```
                ┌────────────────────────┐
                │        Frontend        │
                │  React + Vite + MUI    │
                │  - UploadPanel         │
                │  - DocumentView        │
                │  - Explore (Search)    │
                └──────────┬─────────────┘
                           │ REST/JSON
                           ▼
                ┌────────────────────────┐
                │     Django + DRF       │
                │  /api/upload           │
                │  /api/documents/:id    │
                │  /api/properties/      │
                │  /api/units/           │
                │  /api/citations/...    │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │     Extraction Core    │
                │  pipeline.py           │
                │  parsers.py (OCR, heur)│
                │  genai.py (LLM opt.)   │
                │  ocr.py (PyMuPDF+Tess) │
                └────────────────────────┘
```

---

## Backend (Django/DRF)

### Environment variables (backend)

Create **backend/.env**:

```env
# Django
DJANGO_SECRET_KEY=dev-secret
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# CORS/media
SITE_BASE=http://localhost:8000
MEDIA_ROOT=media
MEDIA_URL=/media/

# Extraction / LLM (optional)
# GENAI_PROVIDER options:
#   - openai_vision  : send first N pages as images
#   - openai         : text-only JSON mode (uses OCRed full-text)
#   - (unset)        : disable LLM, use OCR/heuristics only
GENAI_PROVIDER=openai_vision
OPENAI_API_KEY=sk-...

# How many pages to send to vision
VISION_MAX_PAGES=6
# OPENAI_MODEL defaults to gpt-4o-mini if unset
OPENAI_MODEL=gpt-4o-mini
```

> If you don’t want to use an LLM, **do not set** `GENAI_PROVIDER` / `OPENAI_API_KEY`. The pipeline will still run with OCR & heuristics.

### Setup & Run (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env as above
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

* Backend will serve REST at `http://localhost:8000/api/`
* Uploaded PDFs go to `MEDIA_ROOT` (default `./media`)

**Test upload (curl):**

```bash
curl -F "file=@/path/to/your.pdf" -F "doc_type=auto" http://localhost:8000/api/upload/
# returns: {"document_id": 1, "property_id": 1}
```

### API Routes

* `POST /api/upload/`

  * form fields: `file=<pdf>`, `doc_type` in `{flyer, rent_roll, lease, auto}`
  * creates `Document` row, runs extraction, persists `Property` + `Units` + `Sections` + `FieldCitation`.
* `GET /api/documents/:id/`

  * returns `Document` + its `sections`.
* `GET /api/properties/`

  * filters: `name`, `city`, `state`, `min_units`, `max_rent`, `source_document`
* `GET /api/units/`

  * filters: `property_id`, `beds`
* `GET /api/search?q=...`

  * lightweight text search across properties/units
* `GET /api/citations/<ModelName>/<record_id>/`

  * returns stored bounding-box citations (used for PDF highlights)

### Data Models

* **Document**: `id, doc_type, uploaded_at, pages, file, sections (reverse FK)`
* **Property**: `id, name, address, city, state, zipcode, year_built, sqft, unit_count, cap_rate, source_document`
* **Unit**: `id, property -> FK, unit_number, beds, baths, sqft, rent, status, lease_start, lease_end`
* **Section**: `id, document -> FK, page, title, text, bbox_*`
* **FieldCitation**: `id, model_name, record_id, field_name, page, x0,y0,x1,y1, snippet`

### Extraction Pipeline

**`core/extraction/pipeline.py`** (LLM-only by default):

* If `GENAI_PROVIDER=openai_vision` → `call_openai_vision_on_pdf(path, max_pages)` sends first N pages as images to a vision model in **JSON mode**.
* Else (`GENAI_PROVIDER=openai`) → builds full text via OCR fallback and calls `call_openai_structured(fulltext)` (JSON mode).
* The raw LLM output is **normalized** by `normalize_to_model_schema()`:

  * unknown keys dropped,
  * numbers coerced (e.g., `"2,640"` → `2640`),
  * lists/dicts guaranteed correct shapes.

**Heuristic/OCR bits** (used in text-mode and/or other flows):

* `ocr.py`: rasterize page (PyMuPDF), orientation detection (Tesseract OSD), adaptive thresholding, multi-PSM Tesseract pass, word/line grouping.
* `parsers.py`: optional proximity heuristics for labels (e.g., “SF”, “Year Built”), layout-based sectioning, and fallback full-text assembly.

**Notes**

* If you want the LLM to **fully control** extraction, keep `GENAI_PROVIDER=openai_vision` and skip merging with heuristics.
* If you want a *hint* for the LLM, you can still build `fulltext` and pass it to text-mode (`GENAI_PROVIDER=openai`).

---

## Frontend (React/Vite)

### Environment variables (frontend)

Create **frontend/.env**:

```env
VITE_API_URL=http://localhost:8000/api
```

> The app expects backend at `/api`. Files are served by Django at absolute URLs (e.g., `http://localhost:8000/media/...`). The code includes a `normalizeDocUrl` helper to handle both absolute and relative `file` fields.

### Setup & Run (frontend)

```bash
cd frontend
npm install
npm run dev
```

Visit: `http://localhost:5173/` (or the port Vite prints).

> **Node version**: Use Node 20+ LTS. If you previously had Node 21/odd versions, switch via `nvm use 20`.

### Key Components

* **`UploadPanel`**

  * Renders a file input and optional `doc_type` select.
  * `POST /api/upload/`, then calls `onUploaded()`.

* **`Explore` page**

  * Top search bar (`SearchBar`), then two tables:

    * `PropertyTable` lists properties (server-side filtering on `name` when you type).
    * `UnitTable` shows units for the first selected/visible property.
  * Data hooks: `useProperties`, `useUnits` (React-Query + `api` client).

* **`DocumentView` page**

  * URL: `/documents/:id`
  * Fetches `GET /documents/:id/` and `GET /properties/?source_document=:id`.
  * Loads citations for the property (`/citations/Property/:id/`).
  * Passes into **`SideBySide`**:

    * Left: `PdfViewer` (renders the PDF, highlights bounding boxes).
    * Right: property summary + “Extracted Sections”.

* **`SideBySide`**

  * Two-column layout without Tailwind dependency (works via inline styles/flex fallback if Tailwind is absent).
  * Sticky right column to scroll PDF independently.

* **`PdfViewer`**

  * Renders the PDF (e.g., via `react-pdf` or a custom viewer) and draws highlight overlays using citations’ (page, bbox).

* **Search bar wiring**

  * `SearchBar` is a simple MUI `TextField`.
  * In `Explore`, `query` state drives `useProperties({name: query})`.
  * Backend filters: `name__icontains`.

---

## Typical Workflow

1. **Run backend**

   ```bash
   cd backend
   source .venv/bin/activate
   python manage.py runserver
   ```

2. **Run frontend**

   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload a PDF**

   * In the UI, use **UploadPanel** (or `curl`).
   * You’ll get a `document_id` in the response/logs.

4. **View extraction**

   * Open `/documents/:id` in the UI.
   * Left panel shows the PDF, right panel shows **Property** and **Extracted Sections**.
   * Explore tab lets you search and browse **Properties** and **Units**.

---

## Troubleshooting

**1) PDF shown but right pane stacked below**

* If Tailwind isn’t installed, the grid classes won’t apply. The current `SideBySide` has inline/flex fallback; ensure you’re using the latest component code.
* Also check your container width; if the viewport is narrow (mobile), the layout intentionally stacks.

**2) Tailwind install errors / npx cannot run**

* You don’t need Tailwind for this to work. The layout includes inline CSS.
* If you want Tailwind, use Node 20 LTS and run:

  ```bash
  npm i -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```

  Then wire `postcss.config.js` and `tailwind.config.js`, and add Tailwind directives in your main CSS.

**3) LLM returns empty/weak extraction**

* Ensure `OPENAI_API_KEY` is set and valid.
* Use `GENAI_PROVIDER=openai_vision` for image-heavy flyers (and bump `VISION_MAX_PAGES` if needed).
* Some PDFs are low-res or image-dense; try increasing DPI in OCR (text-mode) or pre-rasterization.
* The system prompt in `genai.py` is intentionally strict: it **must** return JSON. Relax/add examples if needed.

**4) “AttributeError: 'int' object has no attribute 'strip'”**

* This was handled by coercion and normalization: numeric-like fields are passed through `_to_int/_to_float`. Make sure your backend is using the updated `normalize_to_model_schema()` (and that you aren’t manually calling `.strip()` on numeric fields).

**5) Media URL issues**

* Backend returns absolute file URLs (e.g., `http://localhost:8000/media/...`). In the FE we call `normalizeDocUrl()` to handle either absolute or relative. If you changed serializers, ensure the `file` field is a full URL or keep the helper.

**6) CORS errors**

* Ensure `DJANGO_ALLOWED_HOSTS` and your CORS settings allow `localhost:5173`.

---

## Extending

* **Better extraction**

  * Add domain-specific label maps in `parsers.py`.
  * Add few-shot JSON examples into `call_openai_*` system/user prompts.
* **More models**

  * Add a `Tenant`, `Contact`, or `Amenity` model; serialize and render similarly.
* **Auth/Users**

  * Wrap endpoints with token auth; namespaced “projects”.
* **Databases**

  * Switch to Postgres in `settings.py`; run migrations.
