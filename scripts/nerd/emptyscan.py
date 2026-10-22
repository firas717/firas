#!/usr/bin/env python3
"""Find stretches where the scene card (y 500-1180) shows only the background.

Usage: python3 scripts/nerd/emptyscan.py <video.mp4> [--min 0.75]

Prints every empty stretch at least --min seconds long. Single empty frames are
normal (an element entering, a chapter dip); a stretch of a second or more means
a shot whose layers all start late, so fix that shot before delivering.
A map shot whose coastlines are faint can be flagged for under a second: look at
that frame before changing anything.
"""
import argparse
import subprocess

import numpy as np

FPS = 4
W, H = 270, 170
EDGE_MIN = 0.004  # share of strong horizontal edges below which the card counts as empty


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--min", type=float, default=0.75, help="shortest stretch to report, in seconds")
    a = ap.parse_args()
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", a.video,
         "-vf", f"fps={FPS},scale=1080:1920,crop=1080:680:0:500,scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
        check=True, capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
    empty = [(np.abs(np.diff(f, axis=1)) > 25).mean() < EDGE_MIN for f in frames]
    found, start = 0, None
    for i, e in enumerate(empty + [False]):
        if e and start is None:
            start = i
        elif not e and start is not None:
            if (i - start) / FPS >= a.min:
                print(f"empty {start / FPS:.2f}s - {i / FPS:.2f}s")
                found += 1
            start = None
    print("OK: no empty stretches" if not found else f"{found} empty stretch(es)")


if __name__ == "__main__":
    main()
