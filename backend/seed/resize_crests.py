"""Produce web-sized crests from the 500px originals.

The originals are ~28 MB in total, far too heavy to ship to a browser for a
list of fixtures. This writes smaller copies beside them:

    assets/crests/500/<espn_team_id>.png   originals, moved here untouched
    assets/crests/128/<espn_team_id>.png   detail views
    assets/crests/64/<espn_team_id>.png    list rows

Each output is padded to a square on a transparent canvas, so crests of
differing aspect ratios still line up in a grid without the UI special-casing
them. Sources smaller than the target are never upscaled -- they are centred at
their own size instead, which keeps a low-resolution crest soft rather than
blocky.

The small sizes are also quantised to a 255-colour palette. Crests are flat
vector art, so this is visually indistinguishable -- measured at two pixels of
16,384 with a meaningful alpha shift -- while cutting file size by about two
thirds. The 500px originals are left as true-colour RGBA.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.resize_crests --dry-run
    .venv/bin/python -m backend_2.seed.resize_crests
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

CRESTS = Path(__file__).resolve().parent.parent.parent / "assets" / "crests"
ORIGINALS = CRESTS / "500"
SIZES = (128, 64)


def quantize(img: Image.Image) -> Image.Image:
    """255 colours + transparency. Flat artwork survives this untouched."""
    return img.quantize(colors=255, method=Image.FASTOCTREE)


def square(img: Image.Image, size: int) -> Image.Image:
    """Fit onto a transparent size x size canvas, centred, never upscaled."""
    img = img.convert("RGBA")
    scale = min(size / img.width, size / img.height, 1.0)
    if scale < 1.0:
        img = img.resize(
            (max(1, round(img.width * scale)), max(1, round(img.height * scale))),
            Image.LANCZOS,
        )
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-quantize", action="store_true",
                    help="keep the small sizes as true-colour RGBA")
    args = ap.parse_args()

    # First run: move the flat originals into 500/ so every size is a sibling.
    loose = sorted(CRESTS.glob("*.png"))
    if loose and not args.dry_run:
        ORIGINALS.mkdir(parents=True, exist_ok=True)
        for p in loose:
            shutil.move(str(p), str(ORIGINALS / p.name))
        print(f"moved {len(loose)} originals into {ORIGINALS.relative_to(CRESTS.parent)}")
    elif loose:
        print(f"would move {len(loose)} originals into 500/")

    sources = sorted(ORIGINALS.glob("*.png")) if ORIGINALS.is_dir() else loose
    if not sources:
        raise SystemExit("no crests found -- run download_crests first")
    print(f"sources: {len(sources)}")

    if args.dry_run:
        print("--dry-run: nothing written")
        return

    written: dict[int, int] = {}
    for size in SIZES:
        out_dir = CRESTS / str(size)
        out_dir.mkdir(parents=True, exist_ok=True)
        total = 0
        for src in sources:
            with Image.open(src) as img:
                out = square(img, size)
                if not args.no_quantize:
                    out = quantize(out)
                out.save(out_dir / src.name, "PNG", optimize=True)
            total += (out_dir / src.name).stat().st_size
        written[size] = total
        print(f"  {size}px: {len(sources)} files, {total / 1e6:.2f} MB")

    # Refresh the manifest with a path per size.
    manifest_path = CRESTS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for entry in manifest.values():
        espn = entry["espnTeamId"]
        entry["files"] = {
            str(s): f"{s}/{espn}.png"
            for s in (500, *SIZES)
            if (CRESTS / str(s) / f"{espn}.png").exists()
        }
        entry.pop("file", None)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    original_total = sum(p.stat().st_size for p in sources)
    print(f"\noriginals 500px: {original_total / 1e6:.1f} MB")
    for size, total in written.items():
        print(f"  -> {size}px is {total / original_total * 100:.1f}% of that")
    print(f"manifest entries: {len(manifest)}")


if __name__ == "__main__":
    main()
