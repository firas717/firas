#!/usr/bin/env python3
"""Arabic word-level transcription with faster-whisper large-v3 (CPU int8)."""
import json, sys
from faster_whisper import WhisperModel
import soundfile as sf, numpy as np
src, out = sys.argv[1], sys.argv[2]
model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
audio, sr = sf.read(src, dtype="float32")
assert sr == 16000
segs, info = model.transcribe(audio, language="ar", word_timestamps=True, vad_filter=False,
                              beam_size=5, condition_on_previous_text=False,
                              initial_prompt="منجم سان خوسيه في تشيلي، العمال الثلاثة والثلاثون، كبسولة فينيكس، ناسا، لويس أورسوا.")
res = []
for s in segs:
    res.append({"start": s.start, "end": s.end, "text": s.text,
                "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in s.words]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump({"duration": info.duration, "segments": res}, open(out, "w"), ensure_ascii=False, indent=1)
