#!/usr/bin/env python3
"""Tighten pauses in a single-take narration and remap word timings.

usage: cut_voice.py voice48k.wav words.json rules.json out_dir

rules.json:
  {"lead": 0.25, "tail": 0.7, "default_pause": 0.36, "max_keep": 0.40,
   "pauses": [{"before": 18.10, "target": 0.45}, ...]}   # times = original word starts

Silences come from ffmpeg silencedetect (-40 dB, 0.2 s). A silence longer than
max_keep is shortened to default_pause; a rule forces a pause target before the
word that starts at `before` (lengthening with digital silence when needed).
Cuts happen inside silence only, with 6 ms fades, so no word is clipped.
"""
import json, re, subprocess, sys
import numpy as np, soundfile as sf

wav, words_json, rules_json, out = sys.argv[1:5]
x, sr = sf.read(wav)
rules = json.load(open(rules_json))
W = [w for s in json.load(open(words_json))["segments"] for w in s["words"]]

log = subprocess.run(["ffmpeg", "-v", "info", "-i", wav, "-af", "silencedetect=n=-40dB:d=0.2", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", log)]
sil = list(zip(starts, ends))

dur = len(x) / sr
first_word, last_end = W[0]["s"], (sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur)

def frame_rms_min(a, b):
    """time of the quietest 10 ms frame in [a, b]"""
    i0, i1 = int(a * sr), int(b * sr)
    seg = x[i0:i1]; fr = int(0.01 * sr); n = max(1, len(seg) // fr)
    r = np.sqrt((seg[:n * fr].reshape(n, fr) ** 2).mean(1))
    return a + (int(np.argmin(r)) + 0.5) * fr / sr

# pause decisions: list of (orig_a, orig_b, target) where [a,b] is the existing gap
ops = []
forced = {round(p["before"], 2): p["target"] for p in rules["pauses"]}
used = set()
for a, b in sil:
    if b >= dur - 0.05 or a <= 0.01:
        continue
    # word that starts right after this silence
    nxt = min((w for w in W if w["s"] >= a - 0.25), key=lambda w: abs(w["s"] - b), default=None)
    target = None
    for t0, tgt in forced.items():
        if a - 0.6 <= t0 <= b + 0.6:
            target = tgt; used.add(t0)
    if target is None:
        if b - a <= rules["max_keep"]:
            continue
        target = rules["default_pause"]
    ops.append((a, b, target))
for t0, tgt in forced.items():
    if t0 not in used:  # no detected silence: insert at the quietest point near the word start
        c = frame_rms_min(t0 - 0.25, t0 + 0.05)
        ops.append((c, c, tgt))
ops.sort()

# build output by walking original audio
fade = int(0.006 * sr)
pieces, tmap = [], []  # tmap: (orig_a, orig_b, new_a)
cursor = max(0.0, first_word - 0.02)
out_t = rules["lead"]
pieces.append(np.zeros(int(rules["lead"] * sr)))

def take(a, b):
    global out_t
    seg = x[int(a * sr):int(b * sr)].copy()
    if len(seg) > 2 * fade:
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    pieces.append(seg); tmap.append((a, b, out_t)); out_t += len(seg) / sr

for a, b, target in ops:
    gap = b - a
    if gap >= target:   # shorten: keep target/2 after a and target/2 before b
        take(cursor, a + target / 2)
        cursor = b - target / 2
    else:               # lengthen: insert silence in the middle of the gap
        mid = (a + b) / 2
        take(cursor, mid)
        pad = np.zeros(int((target - gap) * sr)); pieces.append(pad); out_t += len(pad) / sr
        cursor = mid
end = min(dur, last_end + 0.12)
take(cursor, end)
pieces.append(np.zeros(int(rules["tail"] * sr))); out_t += rules["tail"]

y = np.concatenate(pieces)
sf.write(f"{out}/voice_cut.wav", y, sr, subtype="FLOAT")

def remap(t):
    for a, b, na in tmap:
        if a - 1e-6 <= t <= b + 1e-6:
            return na + (t - a)
    # inside a removed span -> snap to next kept piece
    nxt = [na for a, b, na in tmap if a > t]
    return nxt[0] if nxt else out_t

words = [{"w": w["w"].strip(), "s": round(remap(w["s"]), 3), "e": round(remap(w["e"]), 3), "os": w["s"]} for w in W]
json.dump({"duration": round(len(y) / sr, 3), "tmap": tmap, "ops": ops, "words": words},
          open(f"{out}/cut.json", "w"), ensure_ascii=False, indent=1)
print(f"original {dur:.2f}s -> cut {len(y)/sr:.2f}s ; {len(ops)} pause edits")
for a, b, t in ops:
    print(f"  gap {a:7.2f}-{b:7.2f} ({b-a:.2f}s) -> {t:.2f}s")
