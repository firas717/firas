#!/usr/bin/env python3
"""Intelligibility check: transcribe voice files with faster-whisper large-v3 and score them against what was said.

usage: asr_cer.py <spoken.json> a.wav [b.wav ...]
Reference = the 'say' text of every sentence in spoken.json. Prints character and word error rates
(Arabic-normalised: no diacritics, unified alef/ya/ta-marbuta) and the mean word confidence.
A restored voice must not score worse than the raw recording.
"""
import json, re, sys
import numpy as np, soundfile as sf, soxr
from faster_whisper import WhisperModel


def norm(t):
    t = re.sub(r'[ً-ْـٰ]', '', t)                     # harakat, tatweel
    t = re.sub('[إأآٱ]', 'ا', t).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')
    t = re.sub(r'[^ء-ي\s]', ' ', t)
    return ' '.join(t.split())


def edits(a, b):
    prev = np.arange(len(b) + 1)
    for i, ca in enumerate(a, 1):
        cur = np.empty_like(prev); cur[0] = i
        sub = prev[:-1] + (np.array(b) != ca)
        for j in range(1, len(b) + 1):
            cur[j] = min(sub[j - 1], prev[j] + 1, cur[j - 1] + 1)
        prev = cur
    return int(prev[-1])


sp = json.load(open(sys.argv[1]))
ref = norm(' '.join(s['say'] for sc in sp['scenes'] for s in sc['sentences']))
m = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4)
for p in sys.argv[2:]:
    x, sr = sf.read(p, dtype='float32')
    x = soxr.resample(x.mean(1) if x.ndim > 1 else x, sr, 16000).astype(np.float32)
    segs, _ = m.transcribe(x, language='ar', beam_size=5, vad_filter=False, condition_on_previous_text=False,
                           word_timestamps=True)
    segs = list(segs)
    hyp = norm(' '.join(s.text for s in segs))
    conf = np.mean([w.probability for s in segs for w in s.words])
    cer = edits(list(ref.replace(' ', '')), list(hyp.replace(' ', ''))) / len(ref.replace(' ', ''))
    wer = edits(ref.split(), hyp.split()) / len(ref.split())
    print(f'{p.split("/")[-1]:<28} CER {cer * 100:5.2f}%  WER {wer * 100:5.2f}%  conf {conf:.3f}', flush=True)
    open(p + '.asr.txt', 'w').write(hyp + '\n')
