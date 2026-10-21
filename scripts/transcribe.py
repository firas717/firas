#!/usr/bin/env python3
"""Arabic word-level transcription with faster-whisper.

Writes <out_dir>/words.json in the HyperFrames import format
([{"id","text","start","end"}]) plus <out_dir>/segments.txt for reading.

Usage:
  python3 scripts/transcribe.py <audio-or-video> <out_dir> [--model large-v3-turbo] [--prompt-file names.txt] [--vad]

The audio is decoded with ffmpeg and passed as a numpy array, which avoids
PyAV decoding issues inside faster-whisper.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


def load_audio(path: str) -> np.ndarray:
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("out_dir")
    p.add_argument("--model", default="large-v3-turbo")
    p.add_argument("--prompt-file", help="text file with proper names / script excerpt to bias spelling")
    p.add_argument("--vad", action="store_true", help="skip long silences (use on raw recordings)")
    a = p.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prompt = Path(a.prompt_file).read_text(encoding="utf-8")[:800] if a.prompt_file else None

    t0 = time.time()
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        load_audio(a.audio), language="ar", word_timestamps=True, beam_size=5,
        condition_on_previous_text=False, initial_prompt=prompt, vad_filter=a.vad,
    )

    words, lines = [], []
    for seg in segments:
        lines.append(f"{seg.start:7.2f}-{seg.end:7.2f}  {seg.text.strip()}")
        for w in seg.words or []:
            words.append({"id": f"w{len(words)}", "text": w.word.strip(),
                          "start": round(w.start, 3), "end": round(w.end, 3)})

    (out / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "segments.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(words)} words, {info.duration:.1f}s audio, {time.time() - t0:.0f}s elapsed -> {out}")


if __name__ == "__main__":
    main()
