import sys, os, requests

API = os.environ.get("API", "http://localhost:8000/api")
FOLDER = sys.argv[1] if len(sys.argv) > 1 else "./sample_pdfs"
for fname in os.listdir(FOLDER):
    if not fname.lower().endswith(".pdf"): continue
    doc_type = "flyer" if "flyer" in fname.lower() else ("rent_roll" if "rent" in fname.lower() else "flyer")
    with open(os.path.join(FOLDER, fname), "rb") as f:
        files = {"file": (fname, f, "application/pdf")}
        data = {"doc_type": doc_type}
        r = requests.post(f"{API}/upload/", files=files, data=data)
        print(fname, r.status_code, r.text)
