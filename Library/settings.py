
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = 'static/'
MEDIA_ROOT=os.path.join(BASE_DIR,'media')
MEDIA_URL='/media/'
MODELS_ROOT=os.path.join(BASE_DIR,'Models')
WHISPER_MODEL_PATH =os.path.join(MODELS_ROOT,'whisper-base')
WHISPER_MODEL_URL='/whisper/'
# TESSERACT_PATH=r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_PATH=r"/usr/bin/tesseract"
OLLAMA_MODEL='llama3.2:1b'
OLLAMA_MODEL_API='http://10.63.34.245:11435/api/generate'
CONNECTION_STRING="postgres://postgres:HUAiXjXTJNXrkAyzgxkdpkjJqzPhpXSK@autorack.proxy.rlwy.net:25335/railway"