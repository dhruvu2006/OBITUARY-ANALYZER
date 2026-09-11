import fitz  # PyMuPDF
from PIL import Image
import io

def get_page_count(pdf_bytes):
    """Returns the total number of pages in the PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count, None
    except Exception as e:
        return 0, f"⚠️ Could not open PDF: {str(e)}"

def extract_page_direct_text(page):
    """Attempts to extract text directly from a PDF page (fast, no OCR)."""
    try:
        text = page.get_text("text")
        return text.strip() if text else ""
    except Exception:
        return ""

def extract_page_as_image(page, zoom=2.0):
    """Renders a PDF page to a high-resolution PIL Image for OCR."""
    try:
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return img, None
    except Exception as e:
        return None, str(e)

def extract_all_pages(pdf_bytes):
    """
    Generator that yields (page_num, pil_image, direct_text) for every page.
    Tries direct text extraction first. Falls back to image-only if text is sparse.
    
    Args:
        pdf_bytes (bytes): Raw bytes of the uploaded PDF.
        
    Yields:
        tuple: (1-indexed page_num: int, image: PIL.Image or None, text: str)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return  # Caller should handle the error

    for i, page in enumerate(doc):
        page_num = i + 1
        
        # Try direct text extraction first (fast path)
        direct_text = extract_page_direct_text(page)
        
        # If direct text is sufficient (more than ~50 meaningful chars), no need for OCR image
        has_good_text = len(direct_text.strip()) > 50
        
        if has_good_text:
            yield page_num, None, direct_text  # No image needed — text is good
        else:
            # Render page to image for OCR fallback
            img, err = extract_page_as_image(page)
            yield page_num, img, direct_text  # direct_text may be empty; caller will OCR the image
    
    doc.close()
