# MoleMapper

Count, characterize, and map skin moles from a 360° "spin" video, then compare
monthly scans to spot anything that's new, growing, or changing shape.

> **⚠️ Not a medical device.** MoleMapper is a personal tracking aid. It cannot
> diagnose skin cancer, and it can miss or mis-measure moles. Any mole that is
> new, growing, changing shape or colour, bleeding, or itching should be shown
> to a dermatologist regardless of what this tool reports.

## How it works

1. **Frame sampling** — evenly samples frames across the clip (4K is downscaled
   to a 1280-px working width; motion-blurred frames are dropped). Because the
   subject spins at a roughly constant speed, each frame's timestamp maps to a
   rotation angle.
2. **Skin segmentation** — isolates the skin region so background, hair, and
   clothing are ignored.
3. **Mole detection** — finds dark spots on skin (morphological black-hat on
   the LAB lightness channel) and measures each one: area, diameter,
   circularity, solidity, eccentricity, asymmetry, border irregularity, colour
   variegation, and contrast — the shape/colour factors inspired by the
   dermatological ABCD checklist.
4. **Body mapping** — models the torso as a rotating cylinder: a mole's frame
   angle plus its horizontal offset across the body gives its fixed *surface
   angle*. The same mole seen in 20 consecutive frames collapses to one point
   on an unwrapped (angle × height) map — that's how duplicates are removed and
   the true count is made. Shape is measured from the frame where the mole
   faces the camera most directly (least foreshortening).
5. **Scan comparison** — matches moles between two scans by map position, then
   flags growth (after correcting for camera-distance differences via the
   median size ratio of all matched moles), shape-metric shifts, new moles, and
   missing ones.

## Setup

```bash
cd MoleMapper
pip install -r requirements.txt
```

## Usage

**Monthly scan** (repeat each month with a new video):

```bash
python -m molemapper scan spin_2026-08.mp4 --out scans/2026-08 --date 2026-08-09
```

This writes `scans/2026-08/` containing:

- `scan.json` — the full mole inventory (positions + shape metrics)
- `report.html` — self-contained report: unwrapped body map + a table of every
  mole with a zoomed crop
- `moles/` — close-up crop of each mole
- `frames/` — annotated video frames showing what was detected where

**Compare two months:**

```bash
python -m molemapper compare scans/2026-07 scans/2026-08 --out changes.html
```

Prints a summary and writes an HTML change report: stable / changed / new /
missing per mole, with the changed and new ones highlighted on the body map.

### Useful options

| Flag | Default | When to change it |
|---|---|---|
| `--revolutions` | 1.0 | Video covers more/less than one full spin |
| `--min-contrast` | 12 | Lower to catch fainter moles (more false positives) |
| `--min-diameter` / `--max-diameter` | 4 / 80 px | Detection size range at working resolution |
| `--min-observations` | 2 | Set to 1 for very short clips |
| `--frames` | 72 | More frames = better dedup, slower |
| `--growth-threshold` (compare) | 0.25 | Relative diameter change to flag |

## Filming tips (consistency matters more than quality)

- Same room, same lighting, same distance from the camera each month —
  diffuse, even light; avoid a single hard lamp that casts shadows.
- One slow, steady full turn (10–20 seconds). Slower = less motion blur.
- Camera fixed on a tripod/shelf at mid-torso height.
- Keep hair and clothing off the skin you want tracked; the tool only maps
  what it can see.
- 1080p is plenty: processing happens at 1280-px width anyway, so you can
  downscale a huge 4K file first (`ffmpeg -i in.mp4 -vf scale=1280:-2 out.mp4`)
  with no loss of accuracy — and a much smaller file.

## Limitations

- Sizes are in **pixels**, not millimetres — absolute size needs a reference
  object in frame (e.g. a sticker of known size), which isn't implemented yet.
  Month-to-month *relative* comparison corrects for camera distance
  automatically.
- The cylinder model fits torsos, arms, and legs; it degrades on shoulders and
  highly curved areas.
- Very fair or very dark skin may need `--min-contrast` tuning; tattoos,
  freckle clusters, and body hair can create false positives.
- Assumes a constant-speed spin; a jerky turn smears the angle assignment.

## Testing

```bash
python tests/test_pipeline.py
```

Renders synthetic spin videos of a skin-toned cylinder with moles at known
positions, then asserts the pipeline recovers the exact count and map
coordinates, classifies an oval mole correctly, and that the comparison flags
a grown mole and a new mole (and nothing else).
