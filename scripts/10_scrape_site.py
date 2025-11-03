import os, uuid, hashlib, time
from urllib.parse import urljoin, urlparse
import trafilatura
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()
DB=os.getenv("DATABASE_URL")

BASE="https://adyashanti.opengatesangha.org/"
LIBRARY_SECTIONS=["teachings/library/writing", "teachings/library/audio", "teachings/library/video"]
ITEMS_PER_PAGE=12

def sha1(s:str)->str:
    return hashlib.sha1(s.encode("utf-8","ignore")).hexdigest()

def allowed(url:str)->bool:
    return urlparse(url).netloc == urlparse(BASE).netloc

def get_paginated_urls(section_path, max_pages=50):
    """Generate paginated URLs for a library section.

    Args:
        section_path (str): Path to library section (e.g., 'teachings/library/writing')
        max_pages (int): Maximum number of pages to fetch

    Yields:
        str: Paginated URL for each page
    """
    for page_num in range(max_pages):
        start_offset = page_num * ITEMS_PER_PAGE
        yield f"{BASE}{section_path}?nstart=1&start={page_num}&sorton=creation_date&sortorder=asc&n={ITEMS_PER_PAGE}"

def extract_links(page, url):
    """Extract links from a page using Playwright browser.

    Args:
        page: Playwright page object
        url: URL to extract links from

    Returns:
        set: Set of URLs found on the page
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait a bit for any dynamic content
        page.wait_for_timeout(2000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a in soup.select("a[href]"):
            href = urljoin(url, a["href"])
            if allowed(href) and href.startswith(BASE):
                links.add(href.split("#")[0])
        return links
    except Exception as e:
        print(f"  Failed to fetch links from {url}: {e}")
        return set()

def clean_text(page, url):
    """Extract clean text content from a web page URL using Playwright.

    Downloads the page content using a browser and extracts main text while
    excluding comments, tables, and other non-essential elements.

    Args:
        page: Playwright page object
        url (str): The URL of the web page to extract text from.

    Returns:
        str or None: The extracted clean text if successful, None if the
        download failed or no content could be extracted.
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for content to load
        page.wait_for_timeout(2000)

        html = page.content()
        if not html: return None
        return trafilatura.extract(html, include_comments=False, include_tables=False)
    except Exception as e:
        print(f"  Failed to extract text from {url}: {e}")
        return None

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
    visited = set()
    frontier = set()

    # Add paginated URLs for each library section
    for section_path in LIBRARY_SECTIONS:
        for paginated_url in get_paginated_urls(section_path):
            frontier.add(paginated_url)

    os.makedirs("data/processed/web", exist_ok=True)

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        with psycopg.connect(DB) as conn:
            while frontier:
                url = frontier.pop()
                if url in visited: continue
                visited.add(url)
                print(f"Crawling: {url}")
                try:
                    text = clean_text(page, url)
                    if not text or len(text) < 400:
                        # Empty or minimal content, might be past the last page
                        print(f"  Skipped (insufficient content: {len(text) if text else 0} chars)")
                        continue
                    title = url.split("/")[-2].replace("-", " ").title() if url.endswith("/") else url.split("?")[0].split("/")[-1].replace("-", " ").title()
                    doc_id = upsert_doc(conn, source_url=url, title=title, content=text)
                    with open(f"data/processed/web/{doc_id}.txt", "w") as f:
                        f.write(text)
                    print(f"  Saved: {title} ({doc_id})")

                    # Extract and follow links from the page
                    links = extract_links(page, url)
                    for link in links:
                        if link not in visited:
                            frontier.add(link)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"ERR: {url} - {e}")

        browser.close()

if __name__=="__main__":
    crawl()
