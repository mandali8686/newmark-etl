import fitz

def find_value_near(words, label_text: str, xpad=40, ypad=12):
    label_hits = [w for w in words if w[4].strip().lower() == label_text.lower()]
    for w in label_hits:
        x0,y0,x1,y1,_,_,_,_ = w
        candidates = []
        for ww in words:
            X0,Y0,X1,Y1,txt, *_ = ww
            if Y0 >= y0 - ypad and Y1 <= y1 + ypad and X0 >= x1 and X0 <= x1 + 400:
                candidates.append(ww)
        if candidates:
            best = sorted(candidates, key=lambda c: c[0])[0]
            return {"value": best[4], "bbox": [best[0], best[1], best[2], best[3]]}
    return None

def sections_from_layout(path: str):
    doc = fitz.open(path)
    sections = []
    for i, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1, text, *rest = b
            if text and len(text.strip()) > 40:  
                sections.append({
                    "page": i,
                    "title": text.strip().split("\n")[0][:80],
                    "text": text.strip(),
                    "bbox": [x0,y0,x1,y1],
                })
    return sections
