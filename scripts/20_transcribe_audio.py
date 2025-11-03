import os, uuid, hashlib
from pathlib import Path
import threading
import time
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
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

"""
tiny: 39M, english only
base: 74M, english only, clear audio
small: 244M, english only, moderate noise
medium: 769M, english only, many speakers/accents
large: 1.5G, multilingual
large-v3-turbo: multilingual, faster than large, slight accuracy drop in some languages compared to large
"""
model = whisperx.load_model("base", device=DEVICE, compute_type=COMPUTE_TYPE)

"""Insert or retrieve an audio transcript document in the database.

Uses the SHA1 hash of the transcript text to determine if a document with
the same content already exists. If found, returns the existing document ID.
Otherwise, creates a new document record with source_type='audio' and
author='Adyashanti'.

Args:
    conn: PostgreSQL database connection object.
    title (str): Title of the audio/document (typically the audio filename
        without extension).
    source_path (Path): Path object pointing to the source audio file.
    transcript_text (str): The transcribed text content from the audio file.
    
Returns:
    uuid.UUID: The document ID, either from an existing document with the
    same content hash or a newly created document.
"""
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

def status_monitor(audio_name, start_time, stop_event):
    """Print status updates every 5 minutes during transcription.
    
    Args:
        audio_name (str): Name of the audio file being transcribed.
        start_time (float): Timestamp when transcription started.
        stop_event (threading.Event): Event to signal when to stop monitoring.
    """
    while not stop_event.is_set():
        if stop_event.wait(timeout=300):  # Wait 5 minutes or until stopped
            break
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"[STATUS] Still transcribing {audio_name}... ({minutes}m {seconds}s elapsed)")

def main():
    with psycopg.connect(DB) as conn:
        audio_files = [f for f in sorted(AUDIO_DIR.glob("*.*"))
                      if f.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']]
        for audio in audio_files:
            stop_event = None
            try:
                print("Transcribing", audio.name)
                start_time = time.time()
                stop_event = threading.Event()

                # Start status monitor thread
                status_thread = threading.Thread(
                    target=status_monitor,
                    args=(audio.name, start_time, stop_event),
                    daemon=True
                )
                status_thread.start()

                result = model.transcribe(str(audio))
                stop_event.set()  # Stop status monitoring

                elapsed = time.time() - start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                print(f"Completed {audio.name} in {minutes}m {seconds}s")

                # WhisperX returns segments, not direct text
                segments = result.get("segments", [])
                text = " ".join([seg.get("text", "") for seg in segments]).strip()
                if not text:
                    print(f"No text found for {audio.name}, skipping")
                    continue
                doc_id = upsert_doc(conn, title=audio.stem, source_path=audio, transcript_text=text)
                (OUT_DIR/f"{doc_id}.txt").write_text(text)
            except Exception as e:
                if stop_event:
                    stop_event.set()  # Stop status monitoring on error
                print("ERR:", audio, e)
                continue  # Skip to next file on error

if __name__=="__main__":
    main()
