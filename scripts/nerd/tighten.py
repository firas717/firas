#!/usr/bin/env python3
"""Shorten pauses in a narration recording and normalise it.

Every pause longer than 0.28 s is cut down to KEEP seconds (half kept on each side,
never inside a word). Then two-pass loudnorm to -16 LUFS / -1.5 dBTP.
Writes <out_dir>/voice_tight.wav, voice_final.wav and timing-map.json.

Usage: python3 scripts/nerd/tighten.py <voice file> <out_dir> [--keep 0.15] [--noise -38]
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

SR = 48000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    ap.add_argument("out")
    ap.add_argument("--keep", type=float, default=0.15)
    ap.add_argument("--noise", type=float, default=-38)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.voice, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    log = subprocess.run(["ffmpeg", "-i", a.voice, "-af", f"silencedetect=noise={a.noise}dB:d=0.28", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(v) for v in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", log)]
    segs, cur = [], 0.0
    for s0, s1 in zip(st, en):
        if s1 - s0 <= a.keep:
            continue
        segs.append((cur, s0 + a.keep / 2))
        cur = s1 - a.keep / 2
    segs.append((cur, len(x) / SR))
    parts, tmap, t = [], [], 0.0
    for s0, s1 in segs:
        i0, i1 = int(s0 * SR), int(s1 * SR)
        parts.append(x[i0:i1])
        tmap.append({"src_start": round(s0, 3), "src_end": round(s1, 3), "out_start": round(t, 3)})
        t += (i1 - i0) / SR
    y = np.concatenate(parts)
    tight = out / "voice_tight.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(tight)],
                   input=y.tobytes(), check=True)
    (out / "timing-map.json").write_text(json.dumps(tmap, indent=0))
    flt = "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=7"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(tight), "-af", flt + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    meas = (f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
            f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tight), "-af", f"{flt}:{meas}", "-ar", str(SR),
                    str(out / "voice_final.wav")], check=True)
    print(f"raw {len(x) / SR:.2f}s -> {t:.2f}s, {len(segs) - 1} pauses shortened")


if __name__ == "__main__":
    main()
