"""Turn per-frame detections into a deduplicated body map.

Model: the torso is approximated as a cylinder rotating in front of the
camera. A mole seen at horizontal offset `s` (-1..1 across the visible body
width) sits at surface angle  frame_angle + asin(s)  on the cylinder. The
same mole is therefore detected in many consecutive frames but always maps
to (roughly) the same (surface_angle, height) point — so clustering in map
space collapses the duplicates into one physical mole.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from .detect import Detection


@dataclass
class Mole:
    mole_id: int
    angle_deg: float          # surface angle around the body, 0..360
    height_norm: float        # 0 = top of skin region, 1 = bottom
    n_observations: int
    # Shape metrics from the best (most face-on) observation:
    diameter_px: float
    area_px: float
    circularity: float
    solidity: float
    eccentricity: float
    asymmetry: float
    border_irregularity: float
    color_variegation: float
    contrast: float
    shape_label: str
    mean_color_lab: tuple[float, float, float]
    best_detection: Detection = field(repr=False, default=None)


def surface_angle(det: Detection) -> float:
    s = float(np.clip(det.surface_offset, -1.0, 1.0))
    return (det.frame_angle_deg + math.degrees(math.asin(s))) % 360.0


def _angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def cluster_moles(
    detections: list[Detection],
    angle_eps_deg: float = 14.0,
    height_eps: float = 0.035,
    min_observations: int = 2,
) -> list[Mole]:
    """Greedy clustering in (surface angle, height) space with angle wraparound.

    `min_observations` >= 2 rejects one-frame flickers (specular glints,
    compression noise): a real mole is visible across several frames of a
    slow spin.
    """
    remaining = list(detections)
    clusters: list[list[Detection]] = []
    while remaining:
        seed = remaining.pop(0)
        members = [seed]
        angle = surface_angle(seed)
        height = seed.height_norm
        changed = True
        while changed:
            changed = False
            keep = []
            for det in remaining:
                if (
                    _angle_diff(surface_angle(det), angle) <= angle_eps_deg
                    and abs(det.height_norm - height) <= height_eps
                ):
                    members.append(det)
                    # Running centroid (circular mean over angles).
                    angles = np.radians([surface_angle(d) for d in members])
                    angle = math.degrees(
                        math.atan2(np.sin(angles).mean(), np.cos(angles).mean())
                    ) % 360.0
                    height = float(np.mean([d.height_norm for d in members]))
                    changed = True
                else:
                    keep.append(det)
            remaining = keep
        clusters.append(members)

    moles: list[Mole] = []
    for members in clusters:
        if len(members) < min_observations:
            continue
        # Measure shape from the most face-on view (smallest |surface_offset|):
        # foreshortening shrinks the apparent width everywhere else.
        best = min(members, key=lambda d: abs(d.surface_offset))
        angles = np.radians([surface_angle(d) for d in members])
        angle = math.degrees(math.atan2(np.sin(angles).mean(), np.cos(angles).mean())) % 360.0
        moles.append(
            Mole(
                mole_id=0,  # assigned after sorting
                angle_deg=float(angle),
                height_norm=float(np.mean([d.height_norm for d in members])),
                n_observations=len(members),
                diameter_px=best.diameter_px,
                area_px=best.area_px,
                circularity=best.circularity,
                solidity=best.solidity,
                eccentricity=best.eccentricity,
                asymmetry=best.asymmetry,
                border_irregularity=best.border_irregularity,
                color_variegation=best.color_variegation,
                contrast=best.contrast,
                shape_label=best.shape_label,
                mean_color_lab=best.mean_color_lab,
                best_detection=best,
            )
        )

    moles.sort(key=lambda mole: (round(mole.height_norm, 2), mole.angle_deg))
    for i, mole in enumerate(moles, start=1):
        mole.mole_id = i
    return moles
