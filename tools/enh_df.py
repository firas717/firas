#!/usr/bin/env python3
"""DeepFilterNet3 denoise (48 kHz). usage: enh_df.py in.wav out.wav [atten_lim_db]"""
import sys, numpy as np, soundfile as sf, torch
from df.enhance import enhance, init_df
x, sr = sf.read(sys.argv[1], dtype='float32')
assert sr == 48000, sr
if x.ndim > 1: x = x.mean(1)
model, st, _ = init_df()
lim = float(sys.argv[3]) if len(sys.argv) > 3 else None
y = enhance(model, st, torch.from_numpy(x)[None], atten_lim_db=lim)[0].numpy()
sf.write(sys.argv[2], y, sr, subtype='FLOAT')
print('ok', len(x) / sr, len(y) / sr)
