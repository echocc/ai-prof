import os
from pathlib import Path
import whisperx
import torch
from dotenv import load_dotenv

load_dotenv()

AUDIO_DIR = Path("data/raw/audio")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

model = whisperx.load_model("base", device=DEVICE, compute_type=COMPUTE_TYPE)

# Get first audio file
audio_files = sorted(AUDIO_DIR.glob("*.*"))
if audio_files:
    first_audio = audio_files[0]
    print(f"Testing with: {first_audio.name}")

    result = model.transcribe(str(first_audio))

    print("\n=== Result keys ===")
    print(result.keys())

    print("\n=== Result structure ===")
    for key, value in result.items():
        if key == "segments":
            print(f"{key}: list with {len(value)} items")
            if value:
                print(f"  First segment: {value[0]}")
        else:
            print(f"{key}: {type(value).__name__} = {value if not isinstance(value, (list, dict)) else '...'}")

    # Try to get text
    text_direct = result.get("text", "")
    print(f"\n=== Direct text access ===")
    print(f"result.get('text', ''): '{text_direct}'")
    print(f"Is empty: {not text_direct}")

    # Try segments
    if "segments" in result:
        segments_text = " ".join([seg.get("text", "") for seg in result["segments"]])
        print(f"\n=== Segments text ===")
        print(f"Combined from segments: '{segments_text[:200]}...'")
