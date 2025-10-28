import os, uuid, hashlib, time
from urllib.parse import urljoin, urlparse
import requests, trafilatura
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DB=os.getenv("DATABASE_URL")

BASE="https://www.adyashanti.org/"
SEEDS=[BASE+"teachings-articles/", BASE+"teachings-audios/", BASE+"teachings-videos/"]

def sha1(s:str)->str:
    return hashlib.sha1(s.encode("utf-8","ignore")).hexdigest()

def allowed(url:str)->bool:
    return urlparse(url).netloc == urlparse(BASE).netloc

def extract_links(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception:
        return set()
    soup=BeautifulSoup(r.text, "html.parser")
    links=set()
    for a in soup.select("a[href]"):
        href=urljoin(url, a["href"])
        if allowed(href) and href.startswith(BASE):
            links.add(href.split("#")[0])
    return links

def clean_text(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded: return None
    return trafilatura.extract(downloaded, include_comments=False, include_tables=False)

def upsert_doc(conn, *, source_url, title, content, published=None):
    h=sha1(content)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM zen_docs WHERE hash=%s", (h,))
        row=cur.fetchone()
        if row: return row["id"]
        doc_id=uuid.uuid4()
        cur.execute("""                INSERT INTO zen_docs (id, source_type, title, author, source_url, published_at, hash)
            VALUES (%s,'web',%s,%s,%s,%s,%s)
        """, (doc_id, title, "Adyashanti", source_url, published, h))
        conn.commit()
        return doc_id

def crawl():
    visited=set()
    frontier=set(SEEDS)
    os.makedirs("data/processed/web", exist_ok=True)
    with psycopg.connect(DB) as conn:
        while frontier:
            url=frontier.pop()
            if url in visited: continue
            visited.add(url)
            try:
                text = clean_text(url)
                if not text or len(text)<400:
                    continue
                title = url.split("/")[-2].replace("-"," ").title() if url.endswith("/") else url
                doc_id = upsert_doc(conn, source_url=url, title=title, content=text)
                with open(f"data/processed/web/{doc_id}.txt","w") as f: f.write(text)
                for link in extract_links(url):
                    if link not in visited: frontier.add(link)
                time.sleep(0.5)
            except Exception as e:
                print("ERR:", url, e)

if __name__=="__main__":
    crawl()
