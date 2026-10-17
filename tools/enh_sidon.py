#!/usr/bin/env python3
"""Speech restoration with Sidon v0.1 (sarulab-speech, MIT) — rebuilds a clean 48 kHz voice from a phone recording.

usage: HF_HOME=<cache> python3 -I enh_sidon.py in.wav out.wav [max_chunk_s=50]
Splits the input only inside silences (so chunk seams are inaudible), restores each chunk, compensates the
model's fixed +8 ms lag and returns a sample-accurate 48 kHz mono float file with the same duration as the input.
"""
import subprocess, sys, time
import numpy as np, soundfile as sf, torch, transformers
from huggingface_hub import hf_hub_download

torch.set_num_threads(4)
SR_IN, SR_OUT, LAG = 16000, 48000, 384          # LAG: measured output delay in 48 kHz samples


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
    t0, parts = time.perf_counter(), []
    with torch.inference_mode():
        for a, b in zip(cuts[:-1], cuts[1:]):
            chunk = torch.nn.functional.pad(torch.from_numpy(wav[a:b]), (0, 24000))  # 1.5 s tail pad (official demo)
            feats = pre(torch.nn.functional.pad(chunk, (160, 160)).numpy(), sampling_rate=SR_IN, return_tensors='pt')
            y = dec(fe(feats['input_features'])['last_hidden_state'].transpose(1, 2)).view(-1).numpy()
            n = (b - a) * 3
            y = np.concatenate([y[LAG:], np.zeros(max(0, n + LAG - len(y)), np.float32)])[:n]
            parts.append(y)
            print(f'  chunk {a / SR_IN:7.2f}-{b / SR_IN:7.2f}s done', flush=True)
    y = np.concatenate(parts).astype(np.float32)
    sf.write(out, y, SR_OUT, subtype='FLOAT')
    print(f'in {len(wav) / SR_IN:.3f}s -> out {len(y) / SR_OUT:.3f}s, cuts {[round(c / SR_IN, 2) for c in cuts]}, '
          f'{time.perf_counter() - t0:.0f}s')


if __name__ == '__main__':
    main(*sys.argv[1:])
