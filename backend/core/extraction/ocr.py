import cv2, pytesseract, fitz, numpy as np

def rasterize_pdf_page(path: str, page_idx: int, dpi=400):
    doc = fitz.open(path)
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]
    return img, pix.width, pix.height

def _osd_rotation(bgr):
    try:
        osd = pytesseract.image_to_osd(bgr)
        import re
        m = re.search(r"Rotate:\s*(\d+)", osd)
        return int(m.group(1)) % 360 if m else 0
    except Exception:
        return 0

def _rotate(bgr, deg):
    if not deg: return bgr
    (h, w) = bgr.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), -deg, 1.0)
    return cv2.warpAffine(bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def _prep_bin(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # invert if mostly dark (white text on dark bg)
    if gray.mean() < 110:
        gray = cv2.bitwise_not(gray)
    # light denoise + local threshold
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    bin_img = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8
    )
    # tiny opening to remove specks
    bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, np.ones((1,1), np.uint8), iterations=1)
    return bin_img

def _deskew(bin_img):
    inv = cv2.bitwise_not(bin_img)
    coords = np.column_stack(np.where(inv > 0))
    if len(coords) < 60:  # not enough signal
        return bin_img
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    (h, w) = bin_img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(bin_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def ocr_words_for_page(path: str, page_idx: int, dpi=400, lang="eng"):
    bgr, px_w, px_h = rasterize_pdf_page(path, page_idx, dpi=dpi)
    rot = _osd_rotation(bgr)
    bgr = _rotate(bgr, rot)
    bin_img = _prep_bin(bgr)
    bin_img = _deskew(bin_img)

    words = []
    scale = 72.0 / dpi
    # try multiple PSMs: 6(block), 4(vertically aligned columns), 11(sparse), 3(auto)
    for psm in (6, 4, 11, 3):
        cfg = f"--psm {psm} --oem 3"
        data = pytesseract.image_to_data(bin_img, lang=lang, config=cfg, output_type=pytesseract.Output.DICT)
        if not data.get("text"): 
            continue
        for i, txt in enumerate(data["text"]):
            txt = (txt or "").strip()
            if not txt:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            words.append([x*scale, y*scale, (x+w)*scale, (y+h)*scale, txt, data.get("block_num",[0])[i], data.get("line_num",[0])[i], data.get("word_num",[0])[i]])
        if len(words) > 8:
            break
    return words

def get_page_words_with_ocr_fallback(doc: fitz.Document, path: str, page_idx: int, dpi=400):
    page = doc[page_idx]
    words = page.get_text("words") or []
    if not words or len(words) < 4:
        try:
            words = ocr_words_for_page(path, page_idx, dpi=dpi)
        except Exception:
            pass
    return words

def get_fulltext_with_ocr_fallback(path: str, dpi=400, lang="eng"):
    doc = fitz.open(path)
    out = []
    for p in range(len(doc)):
        native = doc[p].get_text("text") or ""
        if native.strip():
            out.append(native.strip())
        else:
            ws = ocr_words_for_page(path, p, dpi=dpi, lang=lang)
            if ws:
                # reconstruct as lines by (block,line)
                from collections import defaultdict
                g = defaultdict(list)
                for x0,y0,x1,y1,txt,b,l,w in ws: g[(b,l)].append((x0,txt))
                for _, items in g.items():
                    items.sort(key=lambda t: t[0])
                    out.append(" ".join(t[1] for t in items))
    return "\n".join(out)
