"""Frame extraction from a spin video.

Assumes the subject rotates at a roughly constant speed through the clip and
the clip covers `revolutions` full turns (default 1). Frame timestamps are
converted to rotation angles under that assumption.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Frame:
    index: int          # sample index (0..n_samples-1)
    angle_deg: float    # rotation angle assigned to this frame
    image: np.ndarray   # BGR image, possibly downscaled
    scale: float        # downscale factor applied to the original video


def sample_frames(
    video_path: str,
    n_samples: int = 72,
    revolutions: float = 1.0,
    max_width: int = 1280,
    blur_reject_pct: float = 20.0,
) -> list[Frame]:
    """Sample `n_samples` frames evenly across the clip.

    4K input is downscaled to `max_width` for processing speed; mole
    measurements are made at this working resolution, which is plenty for
    spots a few millimetres across at typical filming distance.

    Frames in the blurriest `blur_reject_pct` percent (motion blur while
    spinning) are dropped, keeping the angle assignment of the survivors.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        raise IOError(f"Video has no readable frames: {video_path}")

    n_samples = min(n_samples, total)
    picks = np.linspace(0, total - 1, n_samples).astype(int)

    frames: list[Frame] = []
    sharpness: list[float] = []
    for i, frame_no in enumerate(picks):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_no))
        ok, img = cap.read()
        if not ok:
            continue
        scale = 1.0
        if img.shape[1] > max_width:
            scale = max_width / img.shape[1]
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        angle = (360.0 * revolutions) * (frame_no / max(total - 1, 1)) % 360.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sharpness.append(cv2.Laplacian(gray, cv2.CV_64F).var())
        frames.append(Frame(index=i, angle_deg=angle, image=img, scale=scale))
    cap.release()

    if not frames:
        raise IOError(f"Could not decode any frames from: {video_path}")

    if blur_reject_pct > 0 and len(frames) > 10:
        cutoff = np.percentile(sharpness, blur_reject_pct)
        kept = [f for f, s in zip(frames, sharpness) if s >= cutoff]
        if kept:
            frames = kept
    return frames
