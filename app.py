import os
import io
import uuid
import subprocess
import re
from flask import Flask, request, render_template, send_file, jsonify, url_for

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pdfplumber
import pandas as pd
from docx import Document
from docx.shared import Inches
from pdf2image import convert_from_path
import pytesseract

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB upload limit

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def save_upload(file_storage):
    ext = os.path.splitext(file_storage.filename)[1] or ".pdf"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(path)
    return path


def new_output_path(suffix, ext=".pdf"):
    return os.path.join(OUTPUT_DIR, f"{uuid.uuid4().hex}_{suffix}{ext}")


# ---------------------------------------------------------------------------
# SEO landing pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/merge-pdf")
def merge_page():
    return render_template("merge.html")


@app.route("/compress-pdf")
def compress_page():
    return render_template("compress.html")

@app.route("/image-tools")
def image_tools_page():
    # This page is entirely client-side (pdf-lib/pdf.js/JSZip run in the
    # browser) -- no upload, no backend processing, no new API endpoint needed.
    return render_template("image_page.html")



@app.route("/pdf-to-excel")
def pdf_to_excel_page():
    return render_template("pdf-to-excel.html")


@app.route("/pdf-to-word")
def pdf_to_word_page():
    return render_template("pdf-to-word.html")


@app.route("/sitemap.xml")
def sitemap():
    return send_file(os.path.join(BASE_DIR, "sitemap.xml"))


@app.route("/robots.txt")
def robots():
    return send_file(os.path.join(BASE_DIR, "robots.txt"))

@app.route("/hello")
def hello():
    # Lightweight keep-alive endpoint for external uptime pingers (UptimeRobot,
    # cron-job.org, etc). Does no PDF work, so it responds instantly and won't
    # eat into request quotas or spin up heavy processing on a schedule.
    return jsonify({"status": "ok"}), 200
 

# ---------------------------------------------------------------------------
# TOOL 1: Merge PDFs (+ optional page numbers + optional watermark in one step)
# ---------------------------------------------------------------------------

@app.route("/api/merge", methods=["POST"])
def api_merge():
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Upload at least 2 PDF files to merge."}), 400

    add_page_numbers = request.form.get("add_page_numbers") == "true"
    watermark_text = request.form.get("watermark_text", "").strip()

    saved_paths = [save_upload(f) for f in files]

    writer = PdfWriter()
    for path in saved_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    total_pages = len(writer.pages)

    # Build overlay (page numbers + watermark) as a single pass
    if add_page_numbers or watermark_text:
        for i, page in enumerate(writer.pages):
            box = page.mediabox
            width, height = float(box.width), float(box.height)

            overlay_buf = io.BytesIO()
            c = canvas.Canvas(overlay_buf, pagesize=(width, height))

            if watermark_text:
                c.saveState()
                c.setFont("Helvetica-Bold", 60)
                c.setFillGray(0.85)
                c.translate(width / 2, height / 2)
                c.rotate(45)
                c.drawCentredString(0, 0, watermark_text)
                c.restoreState()

            if add_page_numbers:
                c.setFont("Helvetica", 10)
                c.setFillGray(0.3)
                c.drawCentredString(width / 2, 20, f"Page {i + 1} of {total_pages}")

            c.save()
            overlay_buf.seek(0)
            overlay_reader = PdfReader(overlay_buf)
            page.merge_page(overlay_reader.pages[0])

    out_path = new_output_path("merged")
    with open(out_path, "wb") as f:
        writer.write(f)

    for p in saved_paths:
        os.remove(p)

    return send_file(out_path, as_attachment=True, download_name="merged.pdf")


# ---------------------------------------------------------------------------
# TOOL 2: Compress PDF to a target size RANGE (e.g. "under 2MB", "200KB-500KB")
# ---------------------------------------------------------------------------

GS_QUALITY_PRESETS = ["/prepress", "/printer", "/ebook", "/screen"]


def gs_compress(input_path, output_path, preset):
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={preset}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


@app.route("/api/compress", methods=["POST"])
def api_compress():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "Upload a PDF file."}), 400

    target_max_kb = request.form.get("target_max_kb", type=int)  # e.g. 2000 for 2MB
    target_min_kb = request.form.get("target_min_kb", type=int, default=0)

    in_path = save_upload(file)
    original_size_kb = os.path.getsize(in_path) / 1024

    best_path = None
    best_size_kb = None

    # Try presets from lightest compression to heaviest, keep the best one
    # that satisfies the target range (or the smallest if no target given).
    for preset in GS_QUALITY_PRESETS:
        candidate = new_output_path(f"compressed_{preset.strip('/')}")
        try:
            gs_compress(in_path, candidate, preset)
        except subprocess.CalledProcessError:
            continue
        size_kb = os.path.getsize(candidate) / 1024

        if target_max_kb:
            if size_kb <= target_max_kb and (target_min_kb == 0 or size_kb >= target_min_kb):
                best_path, best_size_kb = candidate, size_kb
                break  # first preset (least aggressive) that fits the range wins
            # keep the smallest as fallback in case nothing fits the range
            if best_path is None or size_kb < best_size_kb:
                if best_path and best_path != candidate:
                    os.remove(best_path)
                best_path, best_size_kb = candidate, size_kb
            else:
                os.remove(candidate)
        else:
            # No target given: use /ebook as a sane default (good quality/size balance)
            if preset == "/ebook":
                best_path, best_size_kb = candidate, size_kb
            elif best_path is None:
                best_path, best_size_kb = candidate, size_kb
            else:
                os.remove(candidate)

    os.remove(in_path)

    if not best_path:
        return jsonify({"error": "Compression failed."}), 500

    resp = send_file(best_path, as_attachment=True, download_name="compressed.pdf")
    resp.headers["X-Original-Size-KB"] = str(round(original_size_kb, 1))
    resp.headers["X-Compressed-Size-KB"] = str(round(best_size_kb, 1))
    return resp


# ---------------------------------------------------------------------------
# TOOL 3: PDF to Excel/CSV — tuned for bank statements & invoices (tables)
# ---------------------------------------------------------------------------

def clean_number(val):
    if val is None:
        return val
    v = str(val).strip().replace(",", "")
    v = re.sub(r"[^\d.\-()]", "", v)
    if v.startswith("(") and v.endswith(")"):
        v = "-" + v[1:-1]
    try:
        return float(v) if v not in ("", "-", ".") else val
    except ValueError:
        return val


@app.route("/api/pdf-to-excel", methods=["POST"])
def api_pdf_to_excel():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "Upload a PDF file."}), 400

    in_path = save_upload(file)
    all_tables = []

    with pdfplumber.open(in_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables({
                "vertical_strategy": "lines_strict" if page.lines else "text",
                "horizontal_strategy": "lines_strict" if page.lines else "text",
            })
            if not tables:
                # fallback strategy for borderless bank-statement style tables
                tables = page.extract_tables({
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                })
            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
                rows = table[1:]
                df = pd.DataFrame(rows, columns=header)
                # Clean numeric-looking columns (amounts, balances)
                for col in df.columns:
                    lc = col.lower()
                    if any(k in lc for k in ["amount", "balance", "debit", "credit", "total", "qty", "price"]):
                        df[col] = df[col].apply(clean_number)
                df.insert(0, "source_page", page_num)
                all_tables.append(df)

    os.remove(in_path)

    if not all_tables:
        return jsonify({"error": "No tables detected in this PDF. It may be a scanned image — OCR table extraction isn't supported yet."}), 422

    combined = pd.concat(all_tables, ignore_index=True)
    out_path = new_output_path("converted", ext=".xlsx")
    combined.to_excel(out_path, index=False)

    return send_file(out_path, as_attachment=True, download_name="converted.xlsx")


# ---------------------------------------------------------------------------
# TOOL 4: PDF to editable Word — OCR-aware for scanned documents
# ---------------------------------------------------------------------------

def has_extractable_text(path, sample_pages=3):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:sample_pages]:
            if page.extract_text() and page.extract_text().strip():
                return True
    return False


@app.route("/api/pdf-to-word", methods=["POST"])
def api_pdf_to_word():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "Upload a PDF file."}), 400

    force_ocr = request.form.get("force_ocr") == "true"
    in_path = save_upload(file)

    doc = Document()
    use_ocr = force_ocr or not has_extractable_text(in_path)

    if use_ocr:
        images = convert_from_path(in_path, dpi=200)
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            if i > 0:
                doc.add_page_break()
            for line in text.split("\n"):
                if line.strip():
                    doc.add_paragraph(line)
    else:
        with pdfplumber.open(in_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if i > 0:
                    doc.add_page_break()
                for line in text.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line)

    os.remove(in_path)
    out_path = new_output_path("converted", ext=".docx")
    doc.save(out_path)

    resp = send_file(out_path, as_attachment=True, download_name="converted.docx")
    resp.headers["X-Used-OCR"] = "true" if use_ocr else "false"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
