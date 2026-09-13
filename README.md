# PDF Bench

A small Flask application for focused PDF and image conversions. It provides server-side PDF tools alongside a browser-only image toolkit—no accounts or file history required.

## Included tools

- **Merge PDF** — combine two or more PDFs; optionally add page numbers and a watermark.
- **Compress PDF** — compress a PDF with Ghostscript, optionally toward a target size range.
- **PDF to Excel** — extract detected tables into an `.xlsx` spreadsheet, with common numeric columns cleaned.
- **PDF to Word** — extract text into an editable `.docx`; scanned PDFs fall back to OCR.
- **Image tools** — compress or resize images, create PDFs from images, and export PDF pages as images. These run entirely in the browser.

## Requirements

- Python 3.10+
- Ghostscript (PDF compression)
- Tesseract OCR (scanned PDF-to-Word conversion)
- Poppler utilities (rendering PDF pages for OCR)

On Ubuntu/Debian, install the system packages with:

```bash
sudo apt-get update
sudo apt-get install -y ghostscript tesseract-ocr poppler-utils
```

## Run locally

```bash
git clone <your-repository-url>
cd pdf-tools
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

The development server listens on port `5000`. Uploaded files are limited to 50 MB.

## Routes

| Page | API endpoint | Purpose |
| --- | --- | --- |
| `/` | — | Home page |
| `/merge-pdf` | `POST /api/merge` | Merge PDFs |
| `/compress-pdf` | `POST /api/compress` | Compress a PDF |
| `/pdf-to-excel` | `POST /api/pdf-to-excel` | Extract PDF tables to Excel |
| `/pdf-to-word` | `POST /api/pdf-to-word` | Convert PDF text to Word |
| `/image-tools` | — | Client-side image and PDF utilities |
| `/hello` | — | JSON health check |

## Production deployment

Run the app with Gunicorn after installing both Python and system dependencies:

```bash
gunicorn app:app
```

For a Debian-based host, a suitable build command is:

```bash
apt-get update && apt-get install -y ghostscript tesseract-ocr poppler-utils && pip install -r requirements.txt
```

Before launching a public site, replace `https://example.com` in the templates, `sitemap.xml`, and `robots.txt` with the production domain. See [deploy.md](deploy.md) for the original deployment and SEO notes.

## File handling and limitations

Server-side uploads and generated files are stored in `uploads/` and `outputs/` while they are processed. Input files are removed after successful processing; generated files should be cleaned up by the deployment environment or a scheduled cleanup task.

PDF to Excel works best with PDFs containing selectable text and detectable tables. PDF to Word produces editable text, not a pixel-perfect recreation of original layouts, tables, or images. Large conversions are processed synchronously, so a production deployment may eventually benefit from a background job queue.

## Project layout

```text
app.py              Flask routes and PDF-processing logic
requirements.txt    Python dependencies
templates/          Jinja page templates
static/             Stylesheets and browser-side tool scripts
sitemap.xml         Sitemap template
robots.txt          Crawler rules
deploy.md           Deployment and SEO notes
```
