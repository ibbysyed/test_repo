"""Compare two scans (e.g. last month vs this month).

Moles are matched by position on the body map (surface angle + height).
Matched moles are checked for growth and shape change; unmatched moles are
reported as new or missing.
"""

from dataclasses import dataclass


def _angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


@dataclass
class MoleChange:
    old_id: int | None
    new_id: int | None
    status: str            # "stable" | "changed" | "new" | "missing"
    flags: list[str]
    old: dict | None = None
    new: dict | None = None


def compare_scans(
    old_scan: dict,
    new_scan: dict,
    angle_tol_deg: float = 18.0,
    height_tol: float = 0.05,
    growth_threshold: float = 0.25,
    shape_delta_threshold: float = 0.15,
) -> dict:
    """Match moles between scans and flag changes.

    growth_threshold: relative diameter change to flag (0.25 = 25%). Diameter
    is in pixels, so this assumes similar filming distance between scans —
    a systematic size shift across ALL moles indicates framing differences,
    which is estimated and corrected via the median size ratio of matched
    pairs.
    """
    old_moles = list(old_scan["moles"])
    new_moles = list(new_scan["moles"])

    # Greedy nearest-neighbour matching on the body map.
    pairs: list[tuple[dict, dict, float]] = []
    candidates = []
    for om in old_moles:
        for nm in new_moles:
            da = _angle_diff(om["angle_deg"], nm["angle_deg"])
            dh = abs(om["height_norm"] - nm["height_norm"])
            if da <= angle_tol_deg and dh <= height_tol:
                candidates.append((da / angle_tol_deg + dh / height_tol, om, nm))
    candidates.sort(key=lambda c: c[0])
    used_old, used_new = set(), set()
    for cost, om, nm in candidates:
        if om["id"] in used_old or nm["id"] in used_new:
            continue
        used_old.add(om["id"])
        used_new.add(nm["id"])
        pairs.append((om, nm, cost))

    # Correct for framing/distance differences between the two videos.
    ratios = sorted(nm["diameter_px"] / om["diameter_px"] for om, nm, _ in pairs if om["diameter_px"] > 0)
    scale = ratios[len(ratios) // 2] if ratios else 1.0

    changes: list[MoleChange] = []
    for om, nm, _ in pairs:
        flags = []
        adjusted_new_diameter = nm["diameter_px"] / scale if scale > 0 else nm["diameter_px"]
        if om["diameter_px"] > 0:
            rel = (adjusted_new_diameter - om["diameter_px"]) / om["diameter_px"]
            if rel >= growth_threshold:
                flags.append(f"grew ~{rel * 100:.0f}% in diameter")
            elif rel <= -growth_threshold:
                flags.append(f"shrank ~{-rel * 100:.0f}% in diameter")
        for metric, label in (
            ("circularity", "circularity"),
            ("asymmetry", "asymmetry"),
            ("border_irregularity", "border irregularity"),
        ):
            delta = nm[metric] - om[metric]
            if abs(delta) >= shape_delta_threshold:
                direction = "up" if delta > 0 else "down"
                flags.append(f"{label} {direction} ({om[metric]:.2f} -> {nm[metric]:.2f})")
        if om["shape"] != nm["shape"]:
            flags.append(f"shape class {om['shape']} -> {nm['shape']}")
        changes.append(
            MoleChange(
                old_id=om["id"],
                new_id=nm["id"],
                status="changed" if flags else "stable",
                flags=flags,
                old=om,
                new=nm,
            )
        )

    for nm in new_moles:
        if nm["id"] not in used_new:
            changes.append(MoleChange(None, nm["id"], "new", ["not present in previous scan"], None, nm))
    for om in old_moles:
        if om["id"] not in used_old:
            changes.append(
                MoleChange(om["id"], None, "missing", ["not found in this scan (occluded or below detection size?)"], om, None)
            )

    return {
        "old_date": old_scan.get("date"),
        "new_date": new_scan.get("date"),
        "old_count": len(old_moles),
        "new_count": len(new_moles),
        "matched": len(pairs),
        "size_scale_correction": round(scale, 3),
        "changes": [
            {
                "old_id": c.old_id,
                "new_id": c.new_id,
                "status": c.status,
                "flags": c.flags,
                "old": c.old,
                "new": c.new,
            }
            for c in changes
        ],
    }
