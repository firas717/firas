#!/usr/bin/env python3
"""Tag a sound library with AudioSet labels (AST) + simple envelope features.

usage: tag_sounds.py manifest.json out.json
"""
import json, subprocess, sys
import numpy as np, torch
from transformers import ASTFeatureExtractor, ASTForAudioClassification

M = "MIT/ast-finetuned-audioset-10-10-0.4593"
fe = ASTFeatureExtractor.from_pretrained(M)
model = ASTForAudioClassification.from_pretrained(M).eval()
labels = model.config.id2label
torch.set_num_threads(4)

def load(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def features(x, sr=16000):
    fr = int(0.02 * sr); n = max(1, len(x) // fr)
    F = x[:n * fr].reshape(n, fr)
    rms = np.sqrt((F ** 2).mean(1)) + 1e-9
    db = 20 * np.log10(rms)
    peak_i = int(np.argmax(rms))
    active = db > db.max() - 30
    spec = np.abs(np.fft.rfft(F * np.hanning(fr), axis=1)); f = np.fft.rfftfreq(fr, 1 / sr)
    cent = (spec * f).sum(1) / (spec.sum(1) + 1e-9)
    act_idx = np.where(active)[0]
    third = max(1, len(act_idx) // 3)
    c0 = float(np.median(cent[act_idx[:third]])) if len(act_idx) else 0
    c1 = float(np.median(cent[act_idx[-third:]])) if len(act_idx) else 0
    e0 = float(np.median(db[act_idx[:third]])) if len(act_idx) else -90
    e1 = float(np.median(db[act_idx[-third:]])) if len(act_idx) else -90
    flat = np.exp(np.mean(np.log(spec + 1e-9), 1)) / (spec.mean(1) + 1e-9)
    return {
        "peak_t": round(peak_i * 0.02, 2), "attack_s": round(peak_i * 0.02 - (act_idx[0] * 0.02 if len(act_idx) else 0), 2),
        "active_s": round(active.sum() * 0.02, 2), "peak_db": round(float(db.max()), 1),
        "centroid_start": round(c0), "centroid_end": round(c1),
        "level_start_db": round(e0, 1), "level_end_db": round(e1, 1),
        "flatness": round(float(np.median(flat[active])) if active.any() else 0, 3),
    }

man = json.load(open(sys.argv[1]))
out = []
for i, m in enumerate(man):
    x = load(m["path"])
    sr = 16000; win = int(10.24 * sr)
    if len(x) <= win * 1.2:
        starts = [0]
    else:
        k = min(6, int(len(x) / win))
        starts = [int(s) for s in np.linspace(0, len(x) - win, k)]
    probs = []
    for s in starts:
        seg = x[s:s + win]
        inp = fe(seg, sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            probs.append(torch.sigmoid(model(**inp).logits[0]).numpy())
    p = np.mean(probs, 0)
    top = [(labels[j], round(float(p[j]), 3)) for j in np.argsort(-p)[:8]]
    rec = dict(m, top=top, **features(x))
    out.append(rec)
    print(f"{i+1:3d}/{len(man)} {m['id']:<14} {m['dur']:7.2f}s  " + ", ".join(f"{l}:{v:.2f}" for l, v in top[:4]), flush=True)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
