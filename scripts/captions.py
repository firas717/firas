#!/usr/bin/env python3
"""Group corrected word timings into Arabic caption phrases (identity rules).

Optimal segmentation (dynamic programming): phrases of ~1.2-2.6 s and at most two
lines of 28 characters, preferring breaks at punctuation and pauses and never
ending a phrase on a word that needs its continuation (prepositions, particles).

Usage: python3 scripts/captions.py <words_corrected.json> <captions.json>
"""
import json
import sys

DANGLING = {"إلى", "على", "عن", "من", "في", "بعد", "قبل", "لم", "لن", "أن", "بأن", "إن", "ضد", "مع", "حتى",
            "الذي", "التي", "هل", "لا", "ما", "قد", "كان", "كانت", "باسم", "و", "أو", "ثم", "لكن", "بل", "عبارة"}
MAX_CHARS = 52  # two lines of ~26-28 characters


def cost(words, i, j):
    seg = words[i:j + 1]
    text = " ".join(w["text"] for w in seg)
    dur = seg[-1]["end"] - seg[0]["start"]
    if len(text) > MAX_CHARS or dur > 3.4:
        return float("inf")
    c = 0.0
    c += max(0, 1.2 - dur) * 6 + max(0, dur - 2.6) * 4      # duration window
    last = seg[-1]["text"]
    nxt = words[j + 1] if j + 1 < len(words) else None
    gap = (nxt["start"] - seg[-1]["end"]) if nxt else 1.0
    if last.endswith((".", "؟", "…", ":", "!")):
        c -= 2.0
    elif last.endswith("،"):
        c -= 1.0
    elif nxt is not None:
        c += 1.5 - min(gap, 0.4) * 3                       # pauses make better breaks
    if last.strip("،.؟…:") in DANGLING:
        c += 6
    # a phrase should not start with the tail of the previous sentence ("ألمانيا. لو كانت")
    for w in seg[:-1]:
        if w["text"].endswith((".", "؟", "…", ":")):
            c += 3
    return c + 1.0  # per-phrase cost keeps phrases from getting too short


def segment(words):
    n = len(words)
    best = [0.0] + [float("inf")] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - 14), j):
            c = best[i] + cost(words, i, j - 1)
            if c < best[j]:
                best[j], back[j] = c, i
    cuts, j = [], n
    while j > 0:
        cuts.append((back[j], j - 1))
        j = back[j]
    return cuts[::-1]


def main():
    words = json.load(open(sys.argv[1], encoding="utf-8"))
    caps = []
    for i, j in segment(words):
        seg = words[i:j + 1]
        text = " ".join(w["text"] for w in seg).rstrip("،:").strip()
        caps.append({"start": seg[0]["start"], "end": seg[-1]["end"], "text": text})
    json.dump(caps, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in caps:
        print(f"{c['start']:6.2f}-{c['end']:6.2f} ({c['end'] - c['start']:.1f}) {len(c['text']):2d} {c['text']}")


if __name__ == "__main__":
    main()
