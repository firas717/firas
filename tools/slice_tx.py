#!/usr/bin/env python3
"""Re-transcribe audio slices (no prompt, no VAD) to check doubtful words."""
import sys, json, soundfile as sf
from faster_whisper import WhisperModel
audio, sr = sf.read(sys.argv[1], dtype="float32")
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
for spec in sys.argv[2:]:
    a, b = map(float, spec.split(":"))
    seg = audio[int(a * sr):int(b * sr)]
    for temp in (0.0,):
        segs, _ = m.transcribe(seg, language="ar", word_timestamps=True, vad_filter=False, beam_size=5, temperature=temp)
        words = [(round(w.start + a, 2), w.word, round(w.probability, 2)) for s in segs for w in s.words]
        print(f"[{a}-{b}]", " ".join(w[1] for w in words))
        print("   ", words)
