"""Scan persistence: run the full pipeline on a video and save the result as
a scan directory (JSON + mole crops + annotated frames + body map image)."""

import json
import os
from datetime import date

import cv2
import numpy as np

from .detect import detect_moles
from .mapping import Mole, cluster_moles
from .video import sample_frames


def run_scan(
    video_path: str,
    out_dir: str,
    scan_date: str | None = None,
    n_samples: int = 72,
    revolutions: float = 1.0,
    min_diameter_px: float = 4.0,
    max_diameter_px: float = 80.0,
    min_contrast: float = 12.0,
    min_observations: int = 2,
    max_width: int = 1280,
) -> dict:
    """Process a spin video and write a scan directory. Returns the scan dict."""
    os.makedirs(out_dir, exist_ok=True)
    crops_dir = os.path.join(out_dir, "moles")
    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(crops_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)

    frames = sample_frames(
        video_path, n_samples=n_samples, revolutions=revolutions, max_width=max_width
    )
    all_detections = []
    per_frame: dict[int, list] = {}
    for frame in frames:
        dets = detect_moles(
            frame.image,
            frame_index=frame.index,
            frame_angle_deg=frame.angle_deg,
            min_diameter_px=min_diameter_px,
            max_diameter_px=max_diameter_px,
            min_contrast=min_contrast,
        )
        per_frame[frame.index] = dets
        all_detections.extend(dets)

    moles = cluster_moles(all_detections, min_observations=min_observations)

    frame_by_index = {f.index: f for f in frames}
    for mole in moles:
        _save_crop(mole, frame_by_index, crops_dir)
    _save_annotated_frames(moles, frame_by_index, per_frame, frames_dir)

    scan = {
        "schema": 1,
        "date": scan_date or date.today().isoformat(),
        "video": os.path.abspath(video_path),
        "n_frames_used": len(frames),
        "n_raw_detections": len(all_detections),
        "mole_count": len(moles),
        "moles": [_mole_to_dict(m) for m in moles],
    }
    with open(os.path.join(out_dir, "scan.json"), "w") as fh:
        json.dump(scan, fh, indent=2)
    return scan


def load_scan(scan_dir: str) -> dict:
    with open(os.path.join(scan_dir, "scan.json")) as fh:
        return json.load(fh)


def _mole_to_dict(m: Mole) -> dict:
    return {
        "id": m.mole_id,
        "angle_deg": round(m.angle_deg, 2),
        "height_norm": round(m.height_norm, 4),
        "n_observations": m.n_observations,
        "diameter_px": round(m.diameter_px, 2),
        "area_px": round(m.area_px, 1),
        "circularity": round(m.circularity, 3),
        "solidity": round(m.solidity, 3),
        "eccentricity": round(m.eccentricity, 3),
        "asymmetry": round(m.asymmetry, 3),
        "border_irregularity": round(m.border_irregularity, 3),
        "color_variegation": round(m.color_variegation, 2),
        "contrast": round(m.contrast, 1),
        "shape": m.shape_label,
        "mean_color_lab": [round(v, 1) for v in m.mean_color_lab],
        "crop": f"moles/mole_{m.mole_id:03d}.png",
    }


def _save_crop(mole: Mole, frame_by_index: dict, crops_dir: str, pad: int = 24) -> None:
    det = mole.best_detection
    frame = frame_by_index.get(det.frame_index)
    if frame is None:
        return
    img = frame.image
    x, y, w, h = cv2.boundingRect(det.contour)
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
    crop = img[y0:y1, x0:x1].copy()
    shifted = det.contour - [x0, y0]
    cv2.drawContours(crop, [shifted], -1, (0, 255, 0), 1)
    crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(os.path.join(crops_dir, f"mole_{mole.mole_id:03d}.png"), crop)


def _save_annotated_frames(
    moles: list[Mole], frame_by_index: dict, per_frame: dict, frames_dir: str
) -> None:
    """Save each frame that contributed a best-view measurement, with every
    detection outlined and best-view moles labelled by id."""
    best_by_frame: dict[int, list[Mole]] = {}
    for mole in moles:
        best_by_frame.setdefault(mole.best_detection.frame_index, []).append(mole)
    for frame_index, frame_moles in best_by_frame.items():
        frame = frame_by_index.get(frame_index)
        if frame is None:
            continue
        img = frame.image.copy()
        for det in per_frame.get(frame_index, []):
            cv2.drawContours(img, [det.contour], -1, (0, 200, 255), 1)
        for mole in frame_moles:
            det = mole.best_detection
            cv2.drawContours(img, [det.contour], -1, (0, 255, 0), 2)
            cv2.putText(
                img,
                f"#{mole.mole_id}",
                (int(det.cx) + 8, int(det.cy) - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
        cv2.imwrite(
            os.path.join(frames_dir, f"frame_{frame_index:03d}_{frame.angle_deg:05.1f}deg.png"),
            img,
        )
