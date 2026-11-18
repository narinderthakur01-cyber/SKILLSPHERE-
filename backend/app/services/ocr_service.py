import os
import io
import pymupdf as fitz
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from app.core.config import settings

# Configure tesseract cmd if provided or in standard locations
if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
else:
    # Common Windows paths for Tesseract
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
    ]
    for c in candidates:
        if os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            break

def is_tesseract_available() -> bool:
    """Check if tesseract executable is accessible."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def preprocess_image(image: Image.Image) -> Image.Image:
    """Apply grayscale, contrast enhancement, and thresholding for cleaner OCR."""
    # Convert to grayscale
    gray = image.convert("L")
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray)
    contrast_enhanced = enhancer.enhance(2.0)
    # Apply median filter for noise reduction
    denoised = contrast_enhanced.filter(ImageFilter.MedianFilter(size=3))
    return denoised

def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text incrementally:
    1. PyMuPDF digital text extraction page by page.
    2. If extracted text is empty or minimal (< 50 chars), trigger Tesseract OCR fallback on rendered pages.
    """
    pages_text = []
    is_scanned = False
    
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    # 1. Digital PDF extraction
    for page_idx in range(total_pages):
        page = doc.load_page(page_idx)
        text = page.get_text()
        pages_text.append(text.strip())
        
    combined_text = "\n\n".join(pages_text).strip()
    
    # 2. Check if scanned document (minimal or zero text)
    if len(combined_text) < 50:
        is_scanned = True
        pages_text = []
        tess_avail = is_tesseract_available()
        
        for page_idx in range(total_pages):
            page = doc.load_page(page_idx)
            # Render page to high-DPI pixmap
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            if tess_avail:
                processed_img = preprocess_image(img)
                try:
                    ocr_text = pytesseract.image_to_string(processed_img)
                    pages_text.append(ocr_text.strip())
                except Exception as e:
                    pages_text.append(f"[OCR extraction failed for page {page_idx+1}: {str(e)}]")
            else:
                pages_text.append(
                    "[Scanned PDF detected. Install Tesseract OCR for image-based text recognition.]"
                )
        
        combined_text = "\n\n".join(pages_text).strip()
    
    doc.close()
    
    return {
        "text": combined_text,
        "pages": pages_text,
        "page_count": total_pages,
        "is_scanned": is_scanned
    }

def extract_text_from_image(file_path: str) -> dict:
    """Extract text from JPG, JPEG, or PNG using image preprocessing + Tesseract OCR."""
    if not is_tesseract_available():
        return {
            "text": "[Image resume uploaded. Tesseract OCR is required for image extraction.]",
            "pages": [],
            "page_count": 1,
            "is_scanned": True,
            "ocr_available": False
        }
        
    image = Image.open(file_path)
    processed = preprocess_image(image)
    ocr_text = pytesseract.image_to_string(processed)
    
    return {
        "text": ocr_text.strip(),
        "pages": [ocr_text.strip()],
        "page_count": 1,
        "is_scanned": True,
        "ocr_available": True
    }

def extract_resume_text(file_path: str, file_type: str) -> dict:
    """Main extraction dispatcher supporting PDF, JPG, JPEG, PNG."""
    lower_type = file_type.lower()
    if "pdf" in lower_type or file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif any(ext in lower_type or file_path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", "jpg", "jpeg", "png"]):
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_type}. Supported: PDF, JPG, JPEG, PNG.")
