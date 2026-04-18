"""Compose the six dashboard screenshots into an animated GIF.

Each frame is resized to a uniform width, cropped to a consistent height so
the nav stays visually anchored, and written out with per-frame durations.

Usage:
    python scripts/make_gif.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT_GIF = ROOT / "docs" / "dashboard.gif"

FRAMES = [
    ("01-overview.png", 2600),
    ("02-od.png",       2800),
    ("03-speed.png",    2800),
    ("04-journey.png",  2800),
    ("05-map.png",      2800),
    ("06-sources.png",  3200),
]

TARGET_W = 1100
TARGET_H = 800  # top crop


def load_frame(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    ratio = TARGET_W / img.width
    new_h = int(img.height * ratio)
    img = img.resize((TARGET_W, new_h), Image.LANCZOS)
    if img.height > TARGET_H:
        img = img.crop((0, 0, TARGET_W, TARGET_H))
    else:
        canvas = Image.new("RGB", (TARGET_W, TARGET_H), (246, 247, 251))
        canvas.paste(img, (0, 0))
        img = canvas
    return img


def main() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []
    for fname, dur in FRAMES:
        p = SHOTS / fname
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        frames.append(load_frame(p))
        durations.append(dur)
        print(f"  added {fname}  ({dur} ms)")

    if not frames:
        raise SystemExit("No frames found — run the Playwright screenshot step first.")

    OUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=durations,
        loop=0,
        disposal=2,
    )
    print(f"\nWrote {OUT_GIF}  ({OUT_GIF.stat().st_size / 1024:.1f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
