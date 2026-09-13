# PDF Bench

Four working PDF tools in one small Flask app, built for solo-founder speed:

- **Merge PDF** — combine files, optionally add page numbers and/or a watermark in the same step
- **Compress PDF** — shrink a PDF to hit a target size range (e.g. "under 200KB")
- **PDF to Excel** — table extraction tuned for bank statements and invoices, with amount/balance columns cleaned into real numbers
- **PDF to Word** — text extraction that auto-detects scanned pages and switches to OCR

Every page (`/`, `/merge-pdf`, `/compress-pdf`, `/pdf-to-excel`, `/pdf-to-word`) has its own title, meta description, canonical URL, and real explanatory copy — not just an upload box — so each one can independently rank for its own search terms.

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

**System dependencies** (not in requirements.txt, install separately):
- `ghostscript` — powers the Compress tool
- `tesseract-ocr` — powers OCR in the Word tool
- `poppler-utils` — powers PDF-to-image conversion for OCR

On Ubuntu/Debian:
```bash
apt-get install -y ghostscript tesseract-ocr poppler-utils
```

## Deploying it for real

This is a plain Flask app, so it runs on any host that supports Python + system packages: Render, Railway, Fly.io, or a cheap VPS (DigitalOcean/Hetzner). Free static hosts (Vercel/Netlify/GitHub Pages) **won't work** — this needs a real server to run Ghostscript/Tesseract.

Simplest path: Render.com free/starter tier.
1. Push this folder to a GitHub repo.
2. Create a new Render "Web Service" from that repo.
3. Build command: `apt-get update && apt-get install -y ghostscript tesseract-ocr poppler-utils && pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Once deployed, replace every `https://example.com` in `templates/base.html`, each tool template's `canonical` block, `sitemap.xml`, and `robots.txt` with your real domain.

## Before you launch: SEO checklist

- [ ] Swap `example.com` for your real domain everywhere (see above)
- [ ] Submit `yourdomain.com/sitemap.xml` to Google Search Console
- [ ] Each tool page's `<title>` and meta description are already written to target real search phrases people type (e.g. "compress pdf to 200kb") — don't overwrite them with something generic
- [ ] Add a real favicon and social preview image (currently missing — add `og:image` tags in `base.html`)
- [ ] Once you have a domain, get 3-5 backlinks from relevant places (a comment/answer on Reddit or Stack Overflow where someone asks this exact question, your own social bio, a Product Hunt launch)

## What's intentionally left out of this version

To keep this shippable in a weekend instead of a quarter:
- No user accounts, no file history, no payment wall — every tool is free to use as v1. Add a simple usage cap + Stripe paywall later once you see which tool actually gets traffic.
- PDF to Word doesn't preserve tables/images/multi-column layout — it extracts clean text only.
- PDF to Excel reads PDFs with a real text layer; scanned bank statements need OCR added later (the OCR code from the Word tool can be adapted for this).
- No queue/background jobs — large files are processed synchronously. Fine for solo-founder traffic levels; add a job queue (Celery/RQ) if a file starts taking longer than ~20-30 seconds.

## File structure

```
pdf-tools/
  app.py                  # Flask app, all 4 tool endpoints
  requirements.txt
  templates/
    base.html              # shared layout + SEO meta block
    index.html              # homepage listing all tools
    merge.html, compress.html, pdf-to-excel.html, pdf-to-word.html
  static/
    css/style.css
    js/main.js               # shared upload/dropzone helpers
    js/merge.js, compress.js, excel.js, word.js
  sitemap.xml
  robots.txt
```
