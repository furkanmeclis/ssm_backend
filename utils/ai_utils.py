import os
import re
import pytesseract
from PIL import Image
import io
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=openai_api_key)

def is_valid_message(text):
    """Checks text against basic forbidden patterns."""
    if not text: # Handle empty or None text
        return True
    forbidden_patterns = [
        r"hack", r"exploit", r"bypass", r"illegal",
        r"kötüye kullan", r"sistem açığı", r"zararlı kod",
        r"spam", r"phishing", r"malware",
        r"scam", r"fraud"
    ]
    # Case-insensitive check
    return not any(re.search(pattern, text, re.IGNORECASE) for pattern in forbidden_patterns)

def extract_text_from_image(image_file):
    """Extracts text from an uploaded image file using Tesseract."""
    tessdata_path = os.getenv("TESSDATA_DIR_PATH")
    if not tessdata_path:
        print("Warning: TESSDATA_DIR_PATH environment variable not set.")
        tessdata_dir_config = None
    else:
        tessdata_dir_config = f'--tessdata-dir {tessdata_path}'

    try:
        # Check if image_file is already bytes
        if isinstance(image_file, bytes):
            image_bytes = image_file
        # Handle InMemoryUploadedFile or similar Django file objects
        elif hasattr(image_file, 'read'):
            image_bytes = image_file.read()
        else:
             raise ValueError("Unsupported image file type")
        img = Image.open(io.BytesIO(image_bytes))

        # Specify Turkish language and pass the config (if available)
        if tessdata_dir_config:
            text = pytesseract.image_to_string(img, lang='tur', config=tessdata_dir_config)
        else:
            # Run without explicit config if path wasn't found (might fail)
            text = pytesseract.image_to_string(img, lang='tur')
        return text
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract executable not found or not configured correctly.")
        raise RuntimeError("OCR Tesseract engine not found.")
    except Exception as e:
        print(f"Error during OCR process: {e}")
        raise RuntimeError(f"Görüntüden metin çıkarılırken hata oluştu: {str(e)}")

def call_openai_chat(system_prompt, user_message, model="gpt-4.1-nano", max_tokens=512):
    """Calls the OpenAI Chat Completions API."""
    if not client.api_key:
         raise ValueError("OpenAI API Key not configured.")

    if not is_valid_message(user_message):
        return "Etik dışı veya uygunsuz içerik algılandı. Bu tür sorulara yanıt veremem."

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens,
        )
        response_content = completion.choices[0].message.content
        if not is_valid_message(response_content):
             return "AI tarafından üretilen yanıt uygunsuz içerik filtresini geçemedi."
        return response_content

    except OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        raise RuntimeError(f"Yapay zeka ile iletişimde hata oluştu: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during OpenAI call: {e}")
        raise RuntimeError(f"Yapay zeka ile iletişimde beklenmedik bir hata oluştu: {str(e)}")
