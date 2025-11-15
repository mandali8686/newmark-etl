import camelot

def extract_tables(path: str):
    tables = []
    try:
        t1 = camelot.read_pdf(path, pages="all", flavor="lattice")
        tables.extend(list(t1))
    except Exception:
        pass
    try:
        t2 = camelot.read_pdf(path, pages="all", flavor="stream")
        tables.extend(list(t2))
    except Exception:
        pass
    return tables
