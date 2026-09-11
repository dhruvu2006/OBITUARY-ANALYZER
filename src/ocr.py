import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os

# Configure Tesseract path for Windows if not already on system PATH
_TESSERACT_WINDOWS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == 'nt' and os.path.isfile(_TESSERACT_WINDOWS_PATH):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_WINDOWS_PATH


def preprocess_image(image):
    """
    Preprocesses the image to improve OCR accuracy.
    Converts to grayscale, boosts contrast, and sharpens.
    Does not modify the original image.
    """
    try:
        gray = image.convert('L')
        enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        return sharpened
    except Exception as e:
        print(f"Warning: Preprocessing failed, using original image. {e}")
        return image


def run_ocr(image):
    """
    Runs Tesseract OCR on a PIL Image and returns extracted text.
    
    Args:
        image (PIL.Image): The page image to run OCR on.
        
    Returns:
        str: Extracted text, or empty string on failure.
    """
    try:
        processed = preprocess_image(image)
        # PSM 4: Assume a single column of text of variable sizes (good for newspaper columns)
        config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(processed, config=config)
        return text.strip() if text else ""
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return ""
