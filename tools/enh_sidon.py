#!/usr/bin/env python3
"""Speech restoration with Sidon v0.1 (sarulab-speech, MIT) — rebuilds a clean 48 kHz voice from a phone recording.

usage: HF_HOME=<cache> python3 -I enh_sidon.py in.wav out.wav [max_chunk_s=50]
Splits the input only inside silences, restores each chunk with 3 s of context from its neighbours, crossfades the
chunks over 20 ms at the cuts, compensates the model's fixed +8 ms lag and returns a sample-accurate 48 kHz mono
float file with the same duration as the input.
"""
import subprocess, sys, time
import numpy as np, soundfile as sf, torch, transformers
from huggingface_hub import hf_hub_download

torch.set_num_threads(4)
SR_IN, SR_OUT, LAG = 16000, 48000, 384          # LAG: measured output delay in 48 kHz samples
CONTEXT, XF = 3, 160                            # seconds of neighbour context per chunk; half crossfade (16 kHz samples = 10 ms)


def load_16k(path):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', path, '-ac', '1',
           '-af', 'highpass=f=50,aresample=16000:resampler=soxr', '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, np.float32).copy()


def split_points(x, max_s):
    """Chunk boundaries at the centre of the quietest 0.3 s stretch before each max_s limit."""
    hop = SR_IN // 100
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop * 30) / (hop * 30), 'same')[::hop] + 1e-12)
    cuts, start = [0], 0
    while len(x) - start > max_s * SR_IN:
        lo, hi = (start + int(0.6 * max_s * SR_IN)) // hop, (start + max_s * SR_IN) // hop
        c = (lo + int(np.argmin(rms[lo:hi]))) * hop
        cuts.append(c); start = c
    return cuts + [len(x)]


def main(inp, out, max_s='50'):
    pre = transformers.SeamlessM4TFeatureExtractor.from_pretrained('facebook/w2v-bert-2.0')
    fe = torch.jit.load(hf_hub_download('sarulab-speech/sidon-v0.1', 'feature_extractor_cpu.pt'), map_location='cpu').eval()
    dec = torch.jit.load(hf_hub_download('sarulab-speech/sidon-v0.1', 'decoder_cpu.pt'), map_location='cpu').eval()

    wav = load_16k(inp)
    wav = 0.9 * wav / max(np.abs(wav).max(), 1e-7)
    cuts = split_points(wav, int(max_s))
    n_in = len(wav)
    out_y = np.zeros(n_in * 3, np.float64)
    wsum = np.zeros(n_in * 3, np.float64)
    t0 = time.perf_counter()
    with torch.inference_mode():
        for a, b in zip(cuts[:-1], cuts[1:]):
            # each chunk sees CONTEXT seconds of its neighbours, so words near a cut and the silence right after a cut
            # are rebuilt as they are mid-file (no rumble at chunk starts, no weak word endings before a cut)
            a0, b0 = max(0, a - CONTEXT * SR_IN), min(n_in, b + CONTEXT * SR_IN)
            chunk = torch.nn.functional.pad(torch.from_numpy(wav[a0:b0]), (0, 24000))  # 1.5 s tail pad (official demo)
            feats = pre(torch.nn.functional.pad(chunk, (160, 160)).numpy(), sampling_rate=SR_IN, return_tensors='pt')
            y = dec(fe(feats['input_features'])['last_hidden_state'].transpose(1, 2)).view(-1).numpy()
            y = np.concatenate([y[LAG:], np.zeros(max(0, (b0 - a0) * 3 + LAG - len(y)), np.float32)])[:(b0 - a0) * 3]
            # keep [a-XF, b+XF] and crossfade linearly with the neighbour across the cut (inside a silence)
            k0, k1 = max(0, a - XF) * 3, min(n_in, b + XF) * 3
            w = np.ones(k1 - k0)
            if a > 0: w[:6 * XF] = np.linspace(0, 1, 6 * XF)
            if b < n_in: w[-6 * XF:] = np.linspace(1, 0, 6 * XF)
            out_y[k0:k1] += w * y[k0 - a0 * 3:k1 - a0 * 3]
            wsum[k0:k1] += w
            print(f'  chunk {a / SR_IN:7.2f}-{b / SR_IN:7.2f}s done (context {a0 / SR_IN:.2f}-{b0 / SR_IN:.2f})', flush=True)
    y = (out_y / np.maximum(wsum, 1e-9)).astype(np.float32)
    sf.write(out, y, SR_OUT, subtype='FLOAT')
    print(f'in {len(wav) / SR_IN:.3f}s -> out {len(y) / SR_OUT:.3f}s, cuts {[round(c / SR_IN, 2) for c in cuts]}, '
          f'{time.perf_counter() - t0:.0f}s')


if __name__ == '__main__':
    main(*sys.argv[1:])
