import os
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import pdf2image
from concurrent.futures import ThreadPoolExecutor, as_completed

TESSERACT = os.environ.get('TESSERACT')
# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
# pytesseract.pytesseract.tesseract_cmd = TESSERACT  # not required already in PATH

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in environment or .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------------------
# Define Structured Output Model (Pydantic)
# -------------------------------------------------------------
class Address(BaseModel):
    house_number: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    full_address: Optional[str]

class IDCardDetails(BaseModel):
    country: Optional[str]
    document_type: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    dob: Optional[str]
    id_number: Optional[str]

    # Replace old address field
    address: Optional[Address]

    issue_date: Optional[str]
    expiry_date: Optional[str]
    confidence_notes: Optional[str]


# -------------------------------------------------------------
# OCR Step
# -------------------------------------------------------------
def ocr_image(input_obj: str) -> str:
    """Extract text from image using Tesseract OCR"""
    if isinstance(input_obj, str):
        img = Image.open(input_obj)
    else:
        img = input_obj  # already a PIL image
    
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
                    "You are a multilingual, country-agnostic document extraction assistant. "
                    "Your job is to extract clean structured information from noisy OCR text. "

                    "### NAME EXTRACTION RULES ### "
                    "- Indian documents (e.g., Aadhaar, PAN, Voter ID, Driving License) often have a single line full name. "
                    "- If the name appears as three words (e.g., 'Rahul Kumar Sharma'), treat: "
                    "    first_name = first word "
                    "    middle_name = second word "
                    "    last_name = third word "
                    "- If the name appears as two words, treat: "
                    "    first_name = first word "
                    "    last_name = second word "
                    "    middle_name = null "
                    "- Ignore prefixes like 'S/O', 'W/O', 'D/O'. "
                    "- Never guess random names. Extract only from text. "

                    "### ADDRESS EXTRACTION ### "
                    "Extract address as an object with keys: house_number, street, city, state, zip, full_address. "
                    "If you cannot find a field, return null. "

                    "### DOCUMENT TYPE / COUNTRY ### "
                    "Identify document type automatically (Aadhaar Card, Passport, etc.). "
                    "Identify country when possible. If not obvious, return null. "

                    "### GENERAL RULES ### "
                    "- Use only exact logic based on the OCR text. "
                    "- Do NOT hallucinate details. "
                    "- Use ISO dates (YYYY-MM-DD). "
                    "- Output must match the Pydantic model."

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
    ext = os.path.splitext(image_path)[1].lower()  

    print("Extension:", ext)

    if ext == ".pdf":
        print("Pricessing")
        images = pdf2image.convert_from_path(image_path)
        print(images)
    else:
        images = [image_path]

    # ocr_text = ""
    # for pg, img in enumerate(images):
    #     ocr_text += ocr_image(img) + "\n\n"

    ocr_results = [""] * len(images)

    def run_ocr(i_img):
        idx, img = i_img
        return idx, ocr_image(img)

    if len(images) > 1:
        max_workers = min(len(images), 6)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_ocr, (i, img)) for i, img in enumerate(images)]
            for f in as_completed(futures):
                idx, text = f.result()
                ocr_results[idx] = text
    else:
        ocr_results[0] = ocr_image(images[0])

    ocr_text = "\n\n".join(ocr_results)
    
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
