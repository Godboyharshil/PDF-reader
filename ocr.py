import io
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

OCR_CACHE = Path("ocr_cache.json")
MIN_TEXT_LENGTH = 500

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        print("Loading EasyOCR model (first time only, downloads ~100MB)...")
        _reader = easyocr.Reader(["en"], verbose=False)
        print("EasyOCR model ready.")
    return _reader


def load_cache():
    if OCR_CACHE.exists():
        return json.loads(OCR_CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    OCR_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def is_image_pdf(pdf_path):
    doc = fitz.open(str(pdf_path))
    text = "".join(page.get_text() for page in doc).strip()
    return len(text) < MIN_TEXT_LENGTH


def pdf_to_images(pdf_path, dpi=150):
    doc = fitz.open(str(pdf_path))
    return [page.get_pixmap(dpi=dpi).tobytes("png") for page in doc]


def ocr_page(image_bytes, reader):
    image = Image.open(io.BytesIO(image_bytes))
    results = reader.readtext(np.array(image))
    results.sort(key=lambda r: r[0][0][1])
    return "\n".join(result[1] for result in results)


def run_ocr(pdf_path):
    reader = get_reader()
    images = pdf_to_images(pdf_path)
    pages = []
    for i, image_bytes in enumerate(images, 1):
        print(f"    OCR page {i}/{len(images)}...")
        try:
            pages.append(ocr_page(image_bytes, reader))
        except Exception as e:
            print(f"    Page {i} failed: {e}")
            pages.append("")
    return pages


def process_pdfs(pdf_paths):
    cache = load_cache()

    for path in pdf_paths:
        name = Path(path).name
        if name in cache:
            print(f"  {name}: already cached, skipping.")
            continue

        if is_image_pdf(path):
            print(f"  {name}: scanned PDF detected, running OCR...")
            cache[name] = {"type": "ocr", "pages": run_ocr(path)}
            print(f"  {name}: OCR complete.")
        else:
            print(f"  {name}: text layer detected, no OCR needed.")
            cache[name] = {"type": "text_layer"}

        save_cache(cache)

    return cache