"""Mole detection and shape characterization within a single frame."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from .skin import row_extent, skin_mask


@dataclass
class Detection:
    frame_index: int
    frame_angle_deg: float
    cx: float                 # centroid in frame pixels
    cy: float
    area_px: float
    diameter_px: float        # equivalent-circle diameter
    perimeter_px: float
    circularity: float        # 4*pi*A/P^2, 1.0 = perfect circle
    solidity: float           # area / convex hull area
    eccentricity: float       # from fitted ellipse, 0 = circle
    asymmetry: float          # 0 = symmetric, higher = more asymmetric
    border_irregularity: float
    mean_color_lab: tuple[float, float, float]
    color_variegation: float  # std of L channel inside the mole
    contrast: float           # skin brightness minus mole brightness
    shape_label: str
    surface_offset: float     # -1..1 horizontal position across the body width
    height_norm: float        # 0 (top of skin bbox) .. 1 (bottom)
    contour: np.ndarray = field(repr=False, default=None)


def _shape_label(circularity: float, solidity: float, eccentricity: float) -> str:
    if solidity < 0.9 or circularity < 0.6:
        return "irregular"
    if eccentricity > 0.75:
        return "oval"
    return "round"


def _asymmetry(contour: np.ndarray) -> float:
    """Overlap-based asymmetry: rasterize the contour, reflect about its
    principal axes through the centroid, and measure the non-overlapping
    fraction (average of both axes). 0 = perfectly symmetric."""
    x, y, w, h = cv2.boundingRect(contour)
    pad = 2
    canvas = np.zeros((h + 2 * pad, w + 2 * pad), np.uint8)
    shifted = contour - [x - pad, y - pad]
    cv2.drawContours(canvas, [shifted], -1, 255, thickness=cv2.FILLED)
    m = cv2.moments(canvas, binaryImage=True)
    if m["m00"] == 0:
        return 0.0
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    area = np.count_nonzero(canvas)

    scores = []
    for flip_code in (0, 1):  # vertical and horizontal reflection
        flipped = cv2.flip(canvas, flip_code)
        # After flipping, the centroid moves; shift it back onto the original.
        fm = cv2.moments(flipped, binaryImage=True)
        fx, fy = fm["m10"] / fm["m00"], fm["m01"] / fm["m00"]
        mat = np.float32([[1, 0, cx - fx], [0, 1, cy - fy]])
        aligned = cv2.warpAffine(flipped, mat, (canvas.shape[1], canvas.shape[0]))
        inter = np.count_nonzero(cv2.bitwise_and(canvas, aligned))
        scores.append(1.0 - inter / area)
    return float(np.mean(scores))


def detect_moles(
    image_bgr: np.ndarray,
    frame_index: int,
    frame_angle_deg: float,
    min_diameter_px: float = 4.0,
    max_diameter_px: float = 80.0,
    min_contrast: float = 12.0,
    edge_margin: float = 0.85,
) -> list[Detection]:
    """Find dark spots on skin and measure their shape.

    Uses a morphological black-hat (dark features on a lighter background)
    on the LAB lightness channel, restricted to the skin mask. Detections in
    the outer `1 - edge_margin` fringe of the body silhouette are dropped:
    near the silhouette edge the surface curves away from the camera, so
    shapes are foreshortened and lighting is unreliable — the same mole is
    measured properly in the frames where it faces the camera.
    """
    mask = skin_mask(image_bgr)
    bounds = None
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return []
    by0, by1 = ys.min(), ys.max()
    body_h = max(int(by1 - by0), 1)

    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    lightness = lab[:, :, 0]
    lightness = cv2.GaussianBlur(lightness, (5, 5), 0)

    kernel_size = int(max_diameter_px) | 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    blackhat = cv2.morphologyEx(lightness, cv2.MORPH_BLACKHAT, kernel)
    blackhat = cv2.bitwise_and(blackhat, blackhat, mask=mask)

    _, binary = cv2.threshold(blackhat, min_contrast, 255, cv2.THRESH_BINARY)
    binary = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    )

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    detections: list[Detection] = []
    min_area = np.pi * (min_diameter_px / 2) ** 2
    max_area = np.pi * (max_diameter_px / 2) ** 2

    for contour in contours:
        area = cv2.contourArea(contour)
        if not (min_area <= area <= max_area):
            continue
        m = cv2.moments(contour)
        if m["m00"] == 0:
            continue
        cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]

        extent = row_extent(mask, int(cy))
        if extent is None:
            continue
        x_left, x_right = extent
        half_width = max((x_right - x_left) / 2.0, 1.0)
        center_x = (x_left + x_right) / 2.0
        offset = (cx - center_x) / half_width  # -1 .. 1 across the body
        if abs(offset) > edge_margin:
            continue

        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0.0
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0.0

        eccentricity = 0.0
        if len(contour) >= 5:
            (_, _), (minor, major), _ = cv2.fitEllipse(contour)
            if major > 0:
                ratio = min(minor, major) / max(minor, major)
                eccentricity = float(np.sqrt(max(0.0, 1.0 - ratio**2)))

        # Ellipse with same area/eccentricity has the minimal perimeter;
        # excess perimeter over a same-area circle indicates a ragged border.
        equiv_perimeter = 2 * np.pi * np.sqrt(area / np.pi)
        border_irregularity = perimeter / equiv_perimeter if equiv_perimeter > 0 else 1.0

        spot_mask = np.zeros(mask.shape, np.uint8)
        cv2.drawContours(spot_mask, [contour], -1, 255, thickness=cv2.FILLED)
        mean_lab = cv2.mean(lab, mask=spot_mask)[:3]
        inside_l = lab[:, :, 0][spot_mask > 0]
        variegation = float(inside_l.std()) if inside_l.size else 0.0

        ring = cv2.dilate(spot_mask, np.ones((9, 9), np.uint8)) & ~spot_mask & mask
        ring_l = lightness[ring > 0]
        contrast = float(ring_l.mean() - inside_l.mean()) if ring_l.size and inside_l.size else 0.0
        if contrast < min_contrast:
            continue

        diameter = 2 * np.sqrt(area / np.pi)
        asym = _asymmetry(contour)
        detections.append(
            Detection(
                frame_index=frame_index,
                frame_angle_deg=frame_angle_deg,
                cx=float(cx),
                cy=float(cy),
                area_px=float(area),
                diameter_px=float(diameter),
                perimeter_px=float(perimeter),
                circularity=float(circularity),
                solidity=float(solidity),
                eccentricity=eccentricity,
                asymmetry=asym,
                border_irregularity=float(border_irregularity),
                mean_color_lab=tuple(float(v) for v in mean_lab),
                color_variegation=variegation,
                contrast=contrast,
                shape_label=_shape_label(circularity, solidity, eccentricity),
                surface_offset=float(offset),
                height_norm=float((cy - by0) / body_h),
                contour=contour,
            )
        )
    return detections
