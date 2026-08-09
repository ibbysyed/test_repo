"""End-to-end tests on synthetic spin videos.

Run with pytest, or directly:  python tests/test_pipeline.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from molemapper.compare import compare_scans
from molemapper.report import write_comparison_report, write_scan_report
from molemapper.scan import run_scan
from tests.synth import TrueMole, render_spin_video

BASELINE = [
    TrueMole(angle_deg=10,  height=0.15, radius_px=9),
    TrueMole(angle_deg=80,  height=0.30, radius_px=6),
    TrueMole(angle_deg=150, height=0.50, radius_px=12, aspect=1.8),   # oval
    TrueMole(angle_deg=200, height=0.22, radius_px=7),
    TrueMole(angle_deg=250, height=0.70, radius_px=10),
    TrueMole(angle_deg=310, height=0.45, radius_px=5),
    TrueMole(angle_deg=340, height=0.85, radius_px=8),
]

# A month later: mole at 250 deg grew 40%, plus one brand-new mole.
FOLLOWUP = [
    TrueMole(angle_deg=10,  height=0.15, radius_px=9),
    TrueMole(angle_deg=80,  height=0.30, radius_px=6),
    TrueMole(angle_deg=150, height=0.50, radius_px=12, aspect=1.8),
    TrueMole(angle_deg=200, height=0.22, radius_px=7),
    TrueMole(angle_deg=250, height=0.70, radius_px=14),               # grew
    TrueMole(angle_deg=310, height=0.45, radius_px=5),
    TrueMole(angle_deg=340, height=0.85, radius_px=8),
    TrueMole(angle_deg=120, height=0.78, radius_px=7),                # new
]


def _angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _match_truth(scan, true_moles, angle_tol=15, height_tol=0.06):
    """Map each ground-truth mole to the closest detected mole, if any."""
    matched = {}
    for tm in true_moles:
        best = None
        for m in scan["moles"]:
            da = _angle_diff(m["angle_deg"], tm.angle_deg)
            dh = abs(m["height_norm"] - tm.height)
            if da <= angle_tol and dh <= height_tol and (best is None or da < best[1]):
                best = (m, da)
        if best:
            matched[id(tm)] = best[0]
    return matched


def _run(tmp_dir, name, true_moles, scan_date):
    video = os.path.join(tmp_dir, f"{name}.mp4")
    render_spin_video(video, true_moles, n_frames=72)
    return run_scan(video, os.path.join(tmp_dir, name), scan_date=scan_date, n_samples=48)


def test_scan_counts_and_maps_moles():
    tmp_dir = tempfile.mkdtemp(prefix="molemapper_")
    scan = _run(tmp_dir, "baseline", BASELINE, "2026-07-01")

    assert scan["mole_count"] == len(BASELINE), (
        f"expected {len(BASELINE)} moles, got {scan['mole_count']}: "
        f"{[(m['angle_deg'], m['height_norm']) for m in scan['moles']]}"
    )
    matched = _match_truth(scan, BASELINE)
    assert len(matched) == len(BASELINE), "some ground-truth moles were not mapped correctly"

    # The deliberately oval mole should not be classified as round.
    oval_true = BASELINE[2]
    oval = _match_truth(scan, [oval_true])[id(oval_true)]
    assert oval["shape"] in ("oval", "irregular"), f"oval mole classified as {oval['shape']}"
    assert oval["eccentricity"] > 0.5

    report = write_scan_report(scan, os.path.join(tmp_dir, "baseline"))
    assert os.path.getsize(report) > 1000
    print(f"OK scan: {scan['mole_count']} moles, report at {report}")


def test_comparison_flags_growth_and_new_mole():
    tmp_dir = tempfile.mkdtemp(prefix="molemapper_cmp_")
    old = _run(tmp_dir, "july", BASELINE, "2026-07-01")
    new = _run(tmp_dir, "august", FOLLOWUP, "2026-08-01")

    comparison = compare_scans(old, new)
    assert comparison["matched"] == len(BASELINE)

    statuses = {c["status"] for c in comparison["changes"]}
    assert "new" in statuses, "new mole was not reported"

    grown = [
        c for c in comparison["changes"]
        if c["status"] == "changed" and any("grew" in f for f in c["flags"])
    ]
    assert len(grown) == 1, f"expected exactly one grown mole, got: {grown}"
    grown_mole = grown[0]["new"]
    assert _angle_diff(grown_mole["angle_deg"], 250) <= 15
    assert abs(grown_mole["height_norm"] - 0.70) <= 0.06

    new_moles = [c for c in comparison["changes"] if c["status"] == "new"]
    assert len(new_moles) == 1
    assert _angle_diff(new_moles[0]["new"]["angle_deg"], 120) <= 15

    report = write_comparison_report(
        comparison, old, new,
        os.path.join(tmp_dir, "july"), os.path.join(tmp_dir, "august"),
        os.path.join(tmp_dir, "comparison.html"),
    )
    assert os.path.getsize(report) > 1000
    print(f"OK compare: {comparison['matched']} matched, 1 grown, 1 new; report at {report}")


if __name__ == "__main__":
    test_scan_counts_and_maps_moles()
    test_comparison_flags_growth_and_new_mole()
    print("All tests passed.")
