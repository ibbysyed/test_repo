"""Synthetic spin-video generator for testing.

Renders a rotating skin-toned cylinder (a stand-in torso) with moles at
known surface angles/heights, so the pipeline's counts and map coordinates
can be checked against ground truth.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

SKIN_BGR = (140, 170, 215)
BACKGROUND_BGR = (60, 60, 60)


@dataclass
class TrueMole:
    angle_deg: float   # surface angle around the cylinder
    height: float      # 0 (top) .. 1 (bottom of cylinder)
    radius_px: float
    color_bgr: tuple = (40, 60, 90)   # dark brown
    aspect: float = 1.0               # >1 elongates vertically (oval mole)


def render_spin_video(
    path: str,
    moles: list[TrueMole],
    n_frames: int = 72,
    size: tuple[int, int] = (640, 900),   # (width, height)
    cylinder_radius: int = 180,
    fps: int = 24,
) -> None:
    width, height = size
    cx = width // 2
    y_top, y_bot = int(height * 0.08), int(height * 0.92)
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise IOError("Could not open VideoWriter (mp4v codec missing?)")

    for i in range(n_frames):
        phi = 360.0 * i / n_frames  # rotation of the subject this frame
        img = np.full((height, width, 3), BACKGROUND_BGR, np.uint8)

        # Cylinder body with mild lambertian shading.
        xs = np.arange(cx - cylinder_radius, cx + cylinder_radius)
        rel = (xs - cx) / cylinder_radius
        shade = (0.72 + 0.28 * np.sqrt(np.clip(1 - rel**2, 0, 1)))[None, :, None]
        body = (np.array(SKIN_BGR)[None, None, :] * shade).astype(np.uint8)
        img[y_top:y_bot, cx - cylinder_radius : cx + cylinder_radius] = body

        for m in moles:
            delta = math.radians((m.angle_deg - phi + 180) % 360 - 180)
            if abs(delta) >= math.radians(80):   # facing away / grazing
                continue
            x = cx + cylinder_radius * math.sin(delta)
            y = y_top + m.height * (y_bot - y_top)
            ax = max(1, int(round(m.radius_px * math.cos(delta))))  # foreshortened
            ay = max(1, int(round(m.radius_px * m.aspect)))
            cv2.ellipse(img, (int(round(x)), int(round(y))), (ax, ay), 0, 0, 360,
                        m.color_bgr, thickness=cv2.FILLED, lineType=cv2.LINE_AA)

        img = cv2.GaussianBlur(img, (3, 3), 0)
        writer.write(img)
    writer.release()
