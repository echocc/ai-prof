import os, uuid, hashlib
from pathlib import Path
import whisperx
import torch
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DB=os.getenv("DATABASE_URL")

AUDIO_DIR=Path("data/raw/audio")
OUT_DIR=Path("data/processed/audio")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = whisperx.load_model("large-v3-turbo", device=DEVICE)

def upsert_doc(conn, *, title, source_path, transcript_text):
    content_hash = hashlib.sha1(transcript_text.encode("utf-8","ignore")).hexdigest()
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM zen_docs WHERE hash=%s", (content_hash,))
        row=cur.fetchone()
        if row: return row["id"]
        doc_id=uuid.uuid4()
        cur.execute("""                INSERT INTO zen_docs (id, source_type, title, author, source_path, hash)
            VALUES (%s,'audio',%s,%s,%s,%s)
        """,(doc_id, title, "Adyashanti", str(source_path), content_hash))
        conn.commit()
        return doc_id

def main():
    with psycopg.connect(DB) as conn:
        for audio in sorted(AUDIO_DIR.glob("*.*")):
            try:
                print("Transcribing", audio.name)
                result = model.transcribe(str(audio))
                text = result.get("text","").strip()
                if not text:
                    continue
                doc_id = upsert_doc(conn, title=audio.stem, source_path=audio, transcript_text=text)
                (OUT_DIR/f"{doc_id}.txt").write_text(text)
            except Exception as e:
                print("ERR:", audio, e)

if __name__=="__main__":
    main()
