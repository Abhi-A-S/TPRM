import logging
from pathlib import Path
from typing import Dict

import fitz

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> Dict[str, str]:
    """Extract text from each page of a PDF and return a clean raw string."""
    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        logger.error("PDF not found: %s", pdf_path)
        return {"raw_text": ""}

    try:
        document = fitz.open(str(path))
    except RuntimeError as error:
        logger.error("Failed to open PDF: %s", error)
        return {"raw_text": ""}

    if document.page_count == 0:
        logger.warning("PDF contains zero pages: %s", pdf_path)
        return {"raw_text": ""}

    extracted_pages = []
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        page_text = page.get_text("text")
        if page_text:
            extracted_pages.append(page_text.strip())
    document.close()

    raw_text = "\n\n".join(extracted_pages).strip()
    return {"raw_text": raw_text}
