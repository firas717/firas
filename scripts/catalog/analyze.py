#!/usr/bin/env python3
"""Analyze downloaded assets by content (not by filename).

- audio: duration, envelope shape, loudness, AudioSet tags (AST model)
- image: size, alpha, CLIP zero-shot tags
- video: duration/size/fps/alpha, CLIP tags of the middle frame
Writes JSONL records to <out>/{audio,image,video}.jsonl (resumable: skips paths already done).

Usage: python3 scripts/catalog/analyze.py assets work/catalog [--only audio|image|video]
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
from PIL import Image

torch.set_num_threads(4)
AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus"}
IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".psd"}
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
SKIP_DIRS = ("video-ad-editor-main/", "مهارات مفيدة/", "الهوية البصرية الخاصة بي/")

CLIP_LABELS = [
    "light leak overlay", "film burn", "old film dust and scratches", "film grain texture", "vintage film frame",
    "smoke", "fire", "sparks", "explosion", "rain", "snow", "fog", "lens flare", "bokeh lights", "light rays",
    "glitch effect", "tv static noise", "neon lines", "paper texture", "grunge texture", "concrete wall texture",
    "torn paper", "old map", "world map", "country map", "hand-drawn arrow", "arrow", "circle highlight",
    "brush stroke", "paint splatter", "blood splatter", "tree", "animal", "person cutout", "silhouette of a person",
    "icon", "social media logo", "subscribe button", "emoji", "picture frame border", "speech bubble",
    "city at night", "prison", "police", "money", "computer", "skull", "question mark", "warning sign",
    "fingerprint", "magnifying glass", "newspaper", "camera", "calendar", "clock", "island", "mountain",
    "ocean", "desert", "forest", "outer space", "planet", "soldier", "tank", "airplane", "ship", "car",
    "building", "castle", "ancient ruins", "document", "red x mark", "check mark", "abstract background",
    "black background", "green screen", "spotlight", "stage light", "gradient background", "3d text effect",
    "transition wipe", "shape animation", "cartoon illustration", "photograph", "flowers", "bird", "fish",
]


def ffprobe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def pcm(path: Path, start: float = 0.0, dur: float = 10.0) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", str(path), "-t", str(dur),
                          "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def envelope_shape(x: np.ndarray) -> dict:
    if len(x) < 1600:
        return {"shape": "empty"}
    hop = 160  # 10 ms
    frames = len(x) // hop
    rms = np.sqrt(np.mean(x[: frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    peak_i = int(np.argmax(db))
    active = db > db.max() - 30
    onsets = int(np.sum(np.diff((db > db.max() - 12).astype(int)) == 1))
    pos = peak_i / max(frames, 1)
    if active.sum() * 0.01 < 0.6:
        shape = "hit"          # short impact/click
    elif pos > 0.6 and db[: frames // 4].mean() < db.max() - 15:
        shape = "rise"         # riser / build-up / whoosh-in
    elif pos < 0.25 and db[-frames // 4:].mean() < db.max() - 15:
        shape = "decay"        # impact with tail / whoosh-out
    elif onsets >= 6:
        shape = "rhythmic"
    else:
        shape = "sustained"
    return {"shape": shape, "peak_at": round(peak_i * 0.01, 2), "onsets": onsets,
            "peak_dbfs": round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1)}


class AudioTagger:
    def __init__(self):
        from transformers import ASTFeatureExtractor, ASTForAudioClassification
        name = "MIT/ast-finetuned-audioset-10-10-0.4593"
        self.fe = ASTFeatureExtractor.from_pretrained(name)
        self.m = ASTForAudioClassification.from_pretrained(name).eval()

    def tags(self, x: np.ndarray, k: int = 6):
        if len(x) < 1600:
            return []
        with torch.no_grad():
            p = torch.sigmoid(self.m(**self.fe(x, sampling_rate=16000, return_tensors="pt")).logits)[0]
        top = p.topk(k)
        return [(self.m.config.id2label[i.item()], round(s.item(), 2)) for s, i in zip(top.values, top.indices)]


class ImageTagger:
    def __init__(self):
        import open_clip
        self.model, _, self.pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        self.model.eval()
        tok = open_clip.get_tokenizer("ViT-B-32")
        with torch.no_grad():
            t = self.model.encode_text(tok([f"a {label}" for label in CLIP_LABELS]))
        self.text = t / t.norm(dim=-1, keepdim=True)

    def tags(self, img: Image.Image, k: int = 4):
        with torch.no_grad():
            f = self.model.encode_image(self.pre(img).unsqueeze(0))
            f = f / f.norm(dim=-1, keepdim=True)
            p = (100 * f @ self.text.T).softmax(dim=-1)[0]
        top = p.topk(k)
        return [(CLIP_LABELS[i.item()], round(s.item(), 2)) for s, i in zip(top.values, top.indices)]


def on_gray(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (128, 128, 128, 255))
        bg.alpha_composite(img)
        return bg.convert("RGB")
    return img.convert("RGB")


def video_frame(path: Path, t: float) -> Image.Image | None:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                          "-vf", "scale=448:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    if not raw:
        return None
    import io
    return Image.open(io.BytesIO(raw))


def load_done(path: Path) -> set:
    if not path.exists():
        return set()
    return {json.loads(line)["path"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("assets")
    ap.add_argument("out")
    ap.add_argument("--only", choices=["audio", "image", "video"])
    a = ap.parse_args()
    root, out = Path(a.assets), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in root.rglob("*") if p.is_file() and not p.name.endswith(".part"))
    rel = lambda p: str(p.relative_to(root))
    files = [p for p in files if not rel(p).startswith(SKIP_DIRS) and "(Preview)/" not in rel(p)]
    audio = [p for p in files if p.suffix.lower() in AUDIO]
    audio_stems = {p.with_suffix("") for p in audio}
    image = [p for p in files if p.suffix.lower() in IMAGE]
    # Sound-library previews (same stem as an audio file) are not real videos.
    video = [p for p in files if p.suffix.lower() in VIDEO and p.with_suffix("") not in audio_stems]

    if a.only in (None, "audio"):
        dst = out / "audio.jsonl"
        done = load_done(dst)
        todo = [p for p in audio if rel(p) not in done]
        print(f"audio: {len(todo)} to analyze", flush=True)
        if todo:
            tagger = AudioTagger()
            def prep(p):
                meta = ffprobe(p)
                dur = float(meta.get("format", {}).get("duration", 0) or 0)
                start = max(0.0, dur / 2 - 5) if dur > 40 else 0.0
                return p, dur, pcm(p, 0, 10), (pcm(p, start, 10) if start else None)
            with ThreadPoolExecutor(3) as ex, open(dst, "a", encoding="utf-8") as f:
                for n, (p, dur, x, mid) in enumerate(ex.map(prep, todo), 1):
                    rec = {"path": rel(p), "dur": round(dur, 2), **envelope_shape(x), "tags": tagger.tags(x)}
                    if mid is not None:
                        rec["tags_mid"] = tagger.tags(mid, 4)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    if n % 100 == 0:
                        print(f"audio {n}/{len(todo)}", flush=True)

    if a.only in (None, "image", "video"):
        tagger = ImageTagger()

    if a.only in (None, "image"):
        dst = out / "image.jsonl"
        done = load_done(dst)
        todo = [p for p in image if rel(p) not in done]
        print(f"image: {len(todo)} to analyze", flush=True)
        with open(dst, "a", encoding="utf-8") as f:
            for n, p in enumerate(todo, 1):
                rec = {"path": rel(p)}
                try:
                    im = Image.open(p)
                    rec.update(w=im.width, h=im.height, alpha=im.mode in ("RGBA", "LA") or "transparency" in im.info)
                    im.thumbnail((448, 448))
                    rec["tags"] = tagger.tags(on_gray(im))
                except Exception as e:  # noqa: BLE001
                    rec["error"] = str(e)[:120]
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if n % 200 == 0:
                    print(f"image {n}/{len(todo)}", flush=True)

    if a.only in (None, "video"):
        dst = out / "video.jsonl"
        done = load_done(dst)
        todo = [p for p in video if rel(p) not in done]
        print(f"video: {len(todo)} to analyze", flush=True)
        with open(dst, "a", encoding="utf-8") as f:
            for p in todo:
                meta = ffprobe(p)
                vs = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})
                dur = float(meta.get("format", {}).get("duration", 0) or 0)
                pix = vs.get("pix_fmt", "")
                rec = {"path": rel(p), "dur": round(dur, 2), "w": vs.get("width"), "h": vs.get("height"),
                       "fps": vs.get("r_frame_rate"), "codec": vs.get("codec_name"), "pix_fmt": pix,
                       "alpha": any(k in pix for k in ("yuva", "argb", "rgba", "bgra", "gbrap")) or vs.get("codec_name") == "qtrle",
                       "has_audio": any(s.get("codec_type") == "audio" for s in meta.get("streams", []))}
                fr = video_frame(p, dur / 2 if dur else 0)
                if fr is not None:
                    rec["tags"] = tagger.tags(on_gray(fr))
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
