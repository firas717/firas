#!/usr/bin/env python3
"""Final audio mix: voice + quiet ducked music bed + up to 3 sound effects, then -16 LUFS.

Usage:
  python3 scripts/nerd/mix.py voice_final.wav out/mix.wav --dur 164.2 --bed "<music file>" \
     --sfx "<file>@32.1:-8:1.75" --sfx "<file>@69.26:-6" --sfx "<file>@145.5:-11:2.6"
  --sfx is FILE@START_SECONDS[:GAIN_DB[:MAX_LEN_SECONDS]]
The bed is looped to --dur, set to -29 LUFS, faded in/out and ducked under the voice.
"""
import argparse
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--bed")
    ap.add_argument("--bed-lufs", type=float, default=-29)
    ap.add_argument("--sfx", action="append", default=[])
    a = ap.parse_args()
    inputs = ["-i", a.voice]
    chains = [f"[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,apad=whole_dur={a.dur},asplit=2[vo][vosc]"]
    mixin = ["[vo]"]
    n = 1
    if a.bed:
        inputs += ["-stream_loop", "-1", "-i", a.bed]
        chains.append(f"[{n}:a]atrim=0:{a.dur},loudnorm=I={a.bed_lufs}:TP=-6,afade=t=in:d=1.5,"
                      f"afade=t=out:st={a.dur - 1.6:.2f}:d=1.6,aformat=sample_rates=48000:channel_layouts=stereo[bedr];"
                      f"[bedr][vosc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[bed]")
        mixin.append("[bed]")
        n += 1
    for k, spec in enumerate(a.sfx):
        f, rest = spec.rsplit("@", 1)
        p = rest.split(":")
        t0, gain = float(p[0]), float(p[1]) if len(p) > 1 else -8
        trim = f"atrim=0:{p[2]},afade=t=out:st={max(0, float(p[2]) - 0.4):.2f}:d=0.4," if len(p) > 2 else ""
        ms = int(t0 * 1000)
        inputs += ["-i", f]
        chains.append(f"[{n}:a]{trim}volume={gain}dB,adelay={ms}|{ms},aformat=sample_rates=48000:channel_layouts=stereo[s{k}]")
        mixin.append(f"[s{k}]")
        n += 1
    chains.append(f"{''.join(mixin)}amix=inputs={len(mixin)}:duration=first:normalize=0,alimiter=limit=0.84[mix]")
    pre = a.out + ".pre.wav"
    if not a.bed:
        chains[0] = chains[0].replace(",asplit=2[vo][vosc]", "[vo]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "[mix]",
                    "-t", str(a.dur), "-ar", "48000", pre], check=True)
    flt = "loudnorm=I=-16:TP=-1.5:LRA=9"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", flt + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    meas = (f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
            f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", f"{flt}:{meas}", "-ar", "48000", "-c:a", "pcm_s16le", a.out],
                   check=True)
    print("mix ->", a.out)


if __name__ == "__main__":
    main()
