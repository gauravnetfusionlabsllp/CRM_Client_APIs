import os
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI


# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in environment or .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------------------
# Define Structured Output Model (Pydantic)
# -------------------------------------------------------------
class IDCardDetails(BaseModel):
    country: Optional[str]                # e.g. India, USA, UAE
    document_type: Optional[str]          # e.g. Passport, License, National ID
    first_name: Optional[str]             # Extracted first name
    last_name: Optional[str]              # Extracted last name
    full_name: Optional[str]              # Combined version (for validation)
    dob: Optional[str]                    # YYYY-MM-DD format
    id_number: Optional[str]
    address: Optional[str]
    issue_date: Optional[str]
    expiry_date: Optional[str]
    confidence_notes: Optional[str]


# -------------------------------------------------------------
# OCR Step
# -------------------------------------------------------------
def ocr_image(path: str) -> str:
    """Extract text from image using Tesseract OCR"""
    img = Image.open(path)
    text = pytesseract.image_to_string(img, lang="eng")
    return text


# -------------------------------------------------------------
# OpenAI Structured Extraction
# -------------------------------------------------------------
def extract_id_details(ocr_text: str, doc_hint: str = "") -> IDCardDetails:
    """Send OCR text to OpenAI and get structured ID info as Pydantic model"""

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a multilingual, country-agnostic document data extraction assistant. "
                    "Extract structured information (identity or document details) from OCR text. "
                    "You must infer the country and document type automatically based on layout, language, and keywords. "
                    "If the name appears, split it into first_name and last_name properly. "
                    "Also include a full_name field combining them. "
                    "Supported documents include Passport, National ID, Driving License, Residence ID, etc. "
                    "If uncertain, set missing fields as null. Use ISO date format (YYYY-MM-DD) when possible."
                ),
            },
            {
                "role": "user",
                "content": f"""
OCR text extracted from an identity or official document.

Document hint (optional): {doc_hint}

OCR TEXT:
\"\"\"{ocr_text}\"\"\"
""",
            },
        ],
        text_format=IDCardDetails,
    )

    return response.output_parsed


# -------------------------------------------------------------
# Combine OCR + Extraction
# -------------------------------------------------------------
def extract_from_image(image_path: str, doc_hint: str = "") -> dict:
    """Extract document info from any image or scanned document"""
    print(f"[+] Processing: {image_path}")
    ocr_text = ocr_image(image_path)

    print("\n----- OCR TEXT (first 500 chars) -----")
    print(ocr_text[:500])
    print("--------------------------------------\n")

    # Step 1: Send OCR text to OpenAI for structured extraction
    structured = extract_id_details(ocr_text, doc_hint)

    # Step 2: Return structured data
    return {
        "status": "success",
        "errorcode": "",
        "reason": "",
        "httpstatus": 200,
        "result": structured.model_dump(),
    }


# -------------------------------------------------------------
# CLI Entrypoint
# -------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import time
    import json

    if len(sys.argv) < 2:
        print("Usage: python extract_id_structured.py /path/to/image.jpg [optional_hint]")
        sys.exit(1)

    image_path = sys.argv[1]
    doc_hint = sys.argv[2] if len(sys.argv) > 2 else ""

    start_time = time.time()
    result = extract_from_image(image_path, doc_hint)
    end_time = time.time()

    print("----- RESULT -----")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n⏱️ Total extraction time: {end_time - start_time:.2f} seconds")
