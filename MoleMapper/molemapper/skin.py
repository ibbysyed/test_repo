"""Skin segmentation: isolate the person's skin so mole detection ignores
background, hair, and clothing."""

import cv2
import numpy as np


def skin_mask(image_bgr: np.ndarray) -> np.ndarray:
    """Binary mask of skin pixels (255 = skin).

    Combines the classic YCrCb chroma box with an HSV constraint, then keeps
    the largest connected component (the subject) and fills small holes so
    dark moles are not punched out of their own mask.
    """
    ycrcb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)
    mask_ycrcb = cv2.inRange(ycrcb, (0, 133, 77), (255, 180, 127))

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask_hsv = cv2.inRange(hsv, (0, 20, 40), (30, 255, 255))
    mask_hsv |= cv2.inRange(hsv, (160, 20, 40), (180, 255, 255))

    mask = cv2.bitwise_and(mask_ycrcb, mask_hsv)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n > 1:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = np.where(labels == largest, 255, 0).astype(np.uint8)

    # Fill interior holes (moles themselves often fail the chroma test).
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    return filled


def body_bounds(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """Bounding box (x, y, w, h) of the skin region, or None if empty."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def row_extent(mask: np.ndarray, y: int, half_window: int = 8) -> tuple[int, int] | None:
    """Horizontal extent (x_left, x_right) of the skin mask around row y.

    Averaged over a small vertical window for stability; used to convert a
    mole's horizontal offset into a surface angle on the body 'cylinder'.
    """
    y0, y1 = max(0, y - half_window), min(mask.shape[0], y + half_window + 1)
    band = mask[y0:y1]
    cols = np.nonzero(band.any(axis=0))[0]
    if len(cols) == 0:
        return None
    return int(cols[0]), int(cols[-1])
