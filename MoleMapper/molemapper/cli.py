"""Command-line interface.

  python -m molemapper scan spin_2026-08.mp4 --out scans/2026-08
  python -m molemapper compare scans/2026-07 scans/2026-08 --out changes.html
"""

import argparse
import sys

from .compare import compare_scans
from .report import DISCLAIMER, write_comparison_report, write_scan_report
from .scan import load_scan, run_scan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="molemapper",
        description="Count, characterize, and map skin moles from a 360-degree spin video.",
        epilog=DISCLAIMER,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Process a spin video into a scan directory")
    p_scan.add_argument("video", help="Path to the spin video (any format OpenCV can read)")
    p_scan.add_argument("--out", required=True, help="Output scan directory, e.g. scans/2026-08")
    p_scan.add_argument("--date", default=None, help="Scan date (YYYY-MM-DD, default: today)")
    p_scan.add_argument("--frames", type=int, default=72, help="Frames to sample (default 72)")
    p_scan.add_argument(
        "--revolutions", type=float, default=1.0,
        help="Full turns the video covers (default 1.0)",
    )
    p_scan.add_argument("--min-diameter", type=float, default=4.0, help="Min mole diameter, px")
    p_scan.add_argument("--max-diameter", type=float, default=80.0, help="Max mole diameter, px")
    p_scan.add_argument(
        "--min-contrast", type=float, default=12.0,
        help="Min darkness vs surrounding skin (lower = more sensitive, more false positives)",
    )
    p_scan.add_argument(
        "--min-observations", type=int, default=2,
        help="Frames a mole must appear in to count (default 2; use 1 for short/fast clips)",
    )
    p_scan.add_argument(
        "--max-width", type=int, default=1280,
        help="Working resolution; 4K is downscaled to this width (default 1280)",
    )

    p_cmp = sub.add_parser("compare", help="Compare two scan directories")
    p_cmp.add_argument("old_scan", help="Earlier scan directory")
    p_cmp.add_argument("new_scan", help="Later scan directory")
    p_cmp.add_argument("--out", default="comparison.html", help="Output HTML report path")
    p_cmp.add_argument(
        "--growth-threshold", type=float, default=0.25,
        help="Relative diameter change to flag (default 0.25 = 25%%)",
    )

    args = parser.parse_args(argv)

    if args.command == "scan":
        scan = run_scan(
            args.video,
            args.out,
            scan_date=args.date,
            n_samples=args.frames,
            revolutions=args.revolutions,
            min_diameter_px=args.min_diameter,
            max_diameter_px=args.max_diameter,
            min_contrast=args.min_contrast,
            min_observations=args.min_observations,
            max_width=args.max_width,
        )
        report = write_scan_report(scan, args.out)
        print(f"Found {scan['mole_count']} moles "
              f"({scan['n_raw_detections']} detections across {scan['n_frames_used']} frames).")
        print(f"Scan saved to {args.out}")
        print(f"Report: {report}")
        print()
        print(DISCLAIMER)
        return 0

    if args.command == "compare":
        old_scan, new_scan = load_scan(args.old_scan), load_scan(args.new_scan)
        comparison = compare_scans(old_scan, new_scan, growth_threshold=args.growth_threshold)
        report = write_comparison_report(
            comparison, old_scan, new_scan, args.old_scan, args.new_scan, args.out
        )
        changed = sum(1 for c in comparison["changes"] if c["status"] == "changed")
        new = sum(1 for c in comparison["changes"] if c["status"] == "new")
        missing = sum(1 for c in comparison["changes"] if c["status"] == "missing")
        print(f"{comparison['old_count']} -> {comparison['new_count']} moles | "
              f"{comparison['matched']} matched, {changed} changed, {new} new, {missing} missing")
        for c in comparison["changes"]:
            if c["status"] in ("changed", "new"):
                label = f"#{c['new_id']}" if c["new_id"] else f"#{c['old_id']}"
                print(f"  [{c['status'].upper()}] {label}: {'; '.join(c['flags'])}")
        print(f"Report: {report}")
        print()
        print(DISCLAIMER)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
