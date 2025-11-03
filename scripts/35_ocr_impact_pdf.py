"""
OCR PDF Ingestion Script

Converts image-based PDF pages to text using Tesseract OCR.
This script processes scanned PDFs that don't have embedded text layers.

Input:
    - PDF files from: data/raw/ocr/*.pdf

Output:
    - Database records in zen_docs table (source_type='pdf')
    - Plain text files in: data/processed/books/{doc_id}.txt

Process:
    1. For each PDF: Convert all pages to images at 300 DPI
    2. Run Tesseract OCR on each page image
    3. Join all page texts with double newlines
    4. Skip files with less than 500 characters (likely failed OCR)
    5. Calculate SHA1 hash of content for deduplication
    6. Insert new documents into database with author='Adyashanti'
    7. Save extracted text to processed directory

Performance:
    - ~0.5-1.5 seconds per page depending on text density
    - 145-page PDF takes approximately 1-3 minutes

Deduplication:
    - Uses SHA1 content hash to detect duplicate documents
    - If content already exists, returns existing document ID
    - Prevents duplicate processing of the same content

Usage:
    python scripts/35_ocr_impact_pdf.py

Requirements:
    - PostgreSQL database with zen_docs table
    - DATABASE_URL in .env file
    - Tesseract OCR installed (brew install tesseract)
    - Poppler installed (brew install poppler)
    - PDF files in data/raw/ocr/ directory
"""

import os, uuid, hashlib
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import time

load_dotenv()
DB = os.getenv("DATABASE_URL")
OCR_DIR = Path("data/raw/ocr")
OUT_DIR = Path("data/processed/books")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

def upsert_doc(conn, *, title, source_path, content, source_type):
    h = sha1(content)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM zen_docs WHERE hash=%s", (h,))
        row = cur.fetchone()
        if row:
            print(f"Document already exists: {row['id']}")
            return row["id"]
        doc_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO zen_docs (id, source_type, title, author, source_path, hash)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (doc_id, source_type, title, "Adyashanti", str(source_path), h))
        conn.commit()
        return doc_id

def main():
    with psycopg.connect(DB) as conn:
        pdf_files = sorted(OCR_DIR.glob("*.pdf"))

        if not pdf_files:
            print(f"No PDF files found in {OCR_DIR}")
            return

        print(f"Found {len(pdf_files)} PDF files to process\n")

        for pdf_path in pdf_files:
            try:
                print(f"=" * 60)
                print(f"Processing: {pdf_path.name}")
                print(f"=" * 60)

                file_start_time = time.time()

                # Convert PDF to images (all pages at once)
                print("Converting PDF to images...")
                images = convert_from_path(pdf_path, dpi=300)
                print(f"Converted {len(images)} pages to images\n")

                # Run OCR on each page
                texts = []
                for i, image in enumerate(images):
                    page_start = time.time()

                    # Run OCR
                    text = pytesseract.image_to_string(image)
                    texts.append(text)

                    page_time = time.time() - page_start
                    elapsed = time.time() - file_start_time

                    # Progress update every 10 pages
                    if (i + 1) % 10 == 0 or i == 0:
                        print(f"  Page {i+1}/{len(images)} - {page_time:.1f}s - Total elapsed: {elapsed/60:.1f} min")

                print()
                full_text = "\n\n".join(texts)
                print(f"Extracted {len(full_text)} characters")

                if len(full_text) < 500:
                    print(f"WARNING: Extracted text is too short (< 500 characters), skipping {pdf_path.name}")
                    continue

                print("Saving to database and file...")
                doc_id = upsert_doc(
                    conn,
                    title=pdf_path.stem,
                    source_path=pdf_path,
                    content=full_text,
                    source_type="pdf"
                )
                output_file = OUT_DIR / f"{doc_id}.txt"
                output_file.write_text(full_text)

                total_time = time.time() - file_start_time
                print(f"Completed {pdf_path.name} in {total_time/60:.1f} minutes")
                print(f"Saved to: {output_file}")
                print(f"Document ID: {doc_id}\n")

            except Exception as e:
                print(f"ERROR processing {pdf_path.name}: {e}")
                continue

if __name__ == "__main__":
    main()
