#!/usr/bin/env python3
"""Non-intrusive speech quality: DNSMOS P.835 (SIG/BAK/OVRL) + P.808 MOS, and torchaudio SQUIM (STOI/PESQ/SI-SDR).

usage: speech_quality.py [--rms] a.wav [b.wav ...]
Based on microsoft/DNS-Challenge DNSMOS/dnsmos_local.py (polynomial mapping for non-personalised MOS).
"""
import sys, numpy as np, soundfile as sf, librosa, onnxruntime as ort

D = '/opt/dnsmos'
SR, LEN = 16000, 9.01
s_835 = ort.InferenceSession(f'{D}/DNSMOS_DNSMOS_sig_bak_ovr.onnx', providers=['CPUExecutionProvider'])
s_808 = ort.InferenceSession(f'{D}/DNSMOS_DNSMOS_model_v8.onnx', providers=['CPUExecutionProvider'])
p_ovr = np.poly1d([-0.06766283, 1.11546468, 0.04602535])
p_sig = np.poly1d([-0.08397278, 1.22083953, 0.0052439])
p_bak = np.poly1d([-0.13166888, 1.60915514, -0.39604546])

def mel(x):
    m = librosa.feature.melspectrogram(y=x, sr=SR, n_fft=321, hop_length=160, n_mels=120)
    return ((librosa.power_to_db(m, ref=np.max) + 40) / 40).T

def dnsmos(x):
    n = int(LEN * SR)
    if len(x) < n: x = np.pad(x, (0, n - len(x)))
    res = []
    for s in range(0, len(x) - n + 1, SR):
        seg = x[s:s + n].astype(np.float32)
        if np.sqrt((seg ** 2).mean()) < 1e-3:   # skip near-silent windows
            continue
        sig, bak, ovr = s_835.run(None, {'input_1': seg[None]})[0][0]
        p808 = s_808.run(None, {'input_1': mel(seg[:-160])[None].astype(np.float32)})[0][0][0]
        res.append((p_sig(sig), p_bak(bak), p_ovr(ovr), p808))
    return np.mean(res, 0)

def squim(x):
    try:
        import torch, torchaudio
        m = torchaudio.pipelines.SQUIM_OBJECTIVE.get_model()
        out = []
        with torch.no_grad():
            for s0 in (10, 50, 95):                       # three 8 s windows (memory-safe)
                seg = x[SR * s0:SR * (s0 + 8)]
                if len(seg) < SR * 4: continue
                out.append([float(v) for v in m(torch.from_numpy(seg.astype(np.float32))[None])])
        return tuple(np.mean(out, 0))
    except Exception as e:
        return (np.nan, np.nan, np.nan)

def level(x):
    """--rms: same active-speech RMS (-26 dBFS) for every file, so compressed and uncompressed versions are
    compared at equal loudness (peak normalisation would feed the compressed one to the models several dB hotter)."""
    if '--rms' not in sys.argv:
        return x / (np.abs(x).max() + 1e-9) * 0.5
    f = x[:len(x) // 320 * 320].reshape(-1, 320); r = np.sqrt((f ** 2).mean(1))
    act = r[r > r.max() * 10 ** (-35 / 20)]
    return x * (10 ** (-26 / 20) / np.sqrt((act ** 2).mean()))

print(f"{'file':<34} {'SIG':>5} {'BAK':>5} {'OVRL':>5} {'P808':>5} | {'STOI':>5} {'PESQ':>5} {'SISDR':>6}")
for p in [a for a in sys.argv[1:] if not a.startswith('--')]:
    x, sr = sf.read(p, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    x = librosa.resample(x, orig_sr=sr, target_sr=SR)
    x = level(x)
    sig, bak, ovr, p808 = dnsmos(x)
    st, pq, sd = squim(x)
    print(f"{p.split('/')[-1][:34]:<34} {sig:5.2f} {bak:5.2f} {ovr:5.2f} {p808:5.2f} | {st:5.2f} {pq:5.2f} {sd:6.1f}", flush=True)
