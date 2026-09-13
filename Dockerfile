FROM python:3.12-slim

# System dependencies the app actually needs:
# - ghostscript: PDF compression
# - tesseract-ocr: OCR for scanned PDFs (PDF to Word)
# - poppler-utils: PDF-to-image rendering (used by pdf2image for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render sets $PORT at runtime; default to 5000 for local `docker run`.
ENV PORT=5000
EXPOSE 5000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
