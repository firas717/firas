#!/usr/bin/env python3
"""CTC forced alignment of known Arabic text to audio (wav2vec2 xlsr-53 arabic).

usage: align_ctc.py voice.wav spoken.json windows.json out.json
windows.json: [[scene_id, start_s, end_s], ...] in the audio's timeline.
Writes per-word timings: [{"scene", "sent", "w", "s", "e", "score"}].
"""
import json, re, sys
import numpy as np, soundfile as sf, torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"
wav, spoken_json, win_json, out_json = sys.argv[1:5]
proc = Wav2Vec2Processor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
torch.set_num_threads(4)
vocab = proc.tokenizer.get_vocab()
blank = vocab["<pad>"]

x, sr = sf.read(wav)
if x.ndim > 1:
    x = x.mean(1)
if sr != 16000:
    import librosa
    x = librosa.resample(x, orig_sr=sr, target_sr=16000); sr = 16000

def norm(t):
    t = re.sub(r"[ً-ْٰ]", "", t)          # strip tashkeel for robustness
    t = t.replace("ـ", "")
    t = re.sub(r"[^ء-ي ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def align(emis, tokens):
    """Viterbi over CTC trellis (torchaudio tutorial algorithm). emis: T x V log-probs."""
    T, N = emis.shape[0], len(tokens)
    trellis = np.full((T + 1, N + 1), -np.inf); trellis[0, 0] = 0
    trellis[1:, 0] = np.cumsum(emis[:, blank])
    for t in range(T):
        stay = trellis[t, 1:] + emis[t, blank]
        change = trellis[t, :-1] + emis[t, tokens]
        trellis[t + 1, 1:] = np.maximum(stay, change)
    # backtrack
    j, t = N, int(np.argmax(trellis[:, N]))
    path = []
    while j > 0 and t > 0:
        stayed = trellis[t - 1, j] + emis[t - 1, blank]
        changed = trellis[t - 1, j - 1] + emis[t - 1, tokens[j - 1]]
        if changed > stayed:
            path.append((j - 1, t - 1, np.exp(emis[t - 1, tokens[j - 1]]))); j -= 1
        t -= 1
    return path[::-1]

spoken = json.load(open(spoken_json))
windows = {int(s): (a, b) for s, a, b in json.load(open(win_json))}
out = []
for scene in spoken["scenes"]:
    a, b = windows[scene["id"]]
    seg = x[int(a * sr):int(b * sr)]
    inp = proc(seg, sampling_rate=sr, return_tensors="pt").input_values
    with torch.no_grad():
        logits = model(inp).logits[0]
    emis = torch.log_softmax(logits, -1).numpy()
    fps = emis.shape[0] / (len(seg) / sr)
    words, wsent = [], []
    for si, s in enumerate(scene["sentences"]):
        for w in norm(s["say"]).split():
            words.append(w); wsent.append(si)
    tokens, owner = [], []
    for wi, w in enumerate(words):
        for ch in w:
            if ch in vocab:
                tokens.append(vocab[ch]); owner.append(wi)
    path = align(emis, tokens)
    spans = {}
    for tok_i, frame, p in path:
        wi = owner[tok_i]
        s0, e0, ps = spans.get(wi, (frame, frame, []))
        spans[wi] = (min(s0, frame), max(e0, frame), ps + [p])
    for wi, w in enumerate(words):
        if wi not in spans:
            continue
        f0, f1, ps = spans[wi]
        out.append({"scene": scene["id"], "sent": wsent[wi], "w": w,
                    "s": round(a + f0 / fps, 3), "e": round(a + (f1 + 1) / fps, 3),
                    "score": round(float(np.mean(ps)), 3)})
    print(f"scene {scene['id']}: {len(words)} words aligned in [{a:.2f},{b:.2f}]", flush=True)
json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=1)
