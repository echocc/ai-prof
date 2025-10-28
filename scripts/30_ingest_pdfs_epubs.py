import os, uuid, hashlib
from pathlib import Path
from pypdf import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DB=os.getenv("DATABASE_URL")

PDF_DIR=Path("data/raw/pdfs")
EPUB_DIR=Path("data/raw/epubs")
OUT_DIR=Path("data/processed/books"); OUT_DIR.mkdir(parents=True, exist_ok=True)

def sha1(s:str)->str:
    return hashlib.sha1(s.encode("utf-8","ignore")).hexdigest()

def upsert_doc(conn, *, title, source_path, content, source_type):
    h=sha1(content)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM zen_docs WHERE hash=%s", (h,))
        row=cur.fetchone()
        if row: return row["id"]
        doc_id=uuid.uuid4()
        cur.execute("""                INSERT INTO zen_docs (id, source_type, title, author, source_path, hash)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,(doc_id, source_type, title, "Adyashanti", str(source_path), h))
        conn.commit()
        return doc_id

def pdf_to_text(p:Path)->str:
    reader=PdfReader(str(p))
    texts=[]
    for page in reader.pages:
        t=page.extract_text() or ""
        texts.append(t)
    return "\n\n".join(texts)

def epub_to_text(p:Path)->str:
    book=epub.read_epub(str(p))
    texts=[]
    for item in book.get_items():
        if item.get_type()==epub.ITEM_DOCUMENT:
            soup=BeautifulSoup(item.get_body_content(), "html.parser")
            texts.append(soup.get_text(" ", strip=True))
    return "\n\n".join(texts)

def main():
    with psycopg.connect(DB) as conn:
        for pdf in PDF_DIR.glob("*.pdf"):
            try:
                text=pdf_to_text(pdf)
                if len(text)<500: continue
                doc_id=upsert_doc(conn, title=pdf.stem, source_path=pdf, content=text, source_type="pdf")
                (OUT_DIR/f"{doc_id}.txt").write_text(text)
            except Exception as e:
                print("PDF ERR:", pdf, e)

        for eb in EPUB_DIR.glob("*.epub"):
            try:
                text=epub_to_text(eb)
                if len(text)<500: continue
                doc_id=upsert_doc(conn, title=eb.stem, source_path=eb, content=text, source_type="epub")
                (OUT_DIR/f"{doc_id}.txt").write_text(text)
            except Exception as e:
                print("EPUB ERR:", eb, e)

if __name__=="__main__":
    main()
