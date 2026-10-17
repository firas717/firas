#!/usr/bin/env python3
"""Resemble Enhance (denoise + generative enhancement to 44.1 kHz).
usage: enh_resemble.py in.wav out.wav [nfe] [lambd] [tau] [start_s] [dur_s]"""
import sys, time, numpy as np, soundfile as sf, torch
from resemble_enhance.enhancer.inference import enhance
x, sr = sf.read(sys.argv[1], dtype='float32')
if x.ndim > 1: x = x.mean(1)
nfe = int(sys.argv[3]) if len(sys.argv) > 3 else 32
lambd = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
tau = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
if len(sys.argv) > 7:
    a, d = float(sys.argv[6]), float(sys.argv[7]); x = x[int(a * sr):int((a + d) * sr)]
torch.set_num_threads(4)
t0 = time.time()
y, osr = enhance(torch.from_numpy(x), sr, 'cpu', nfe=nfe, solver='midpoint', lambd=lambd, tau=tau)
sf.write(sys.argv[2], y.cpu().numpy(), osr, subtype='FLOAT')
print('ok', osr, len(x) / sr, y.shape[-1] / osr, f'{time.time() - t0:.1f}s')
