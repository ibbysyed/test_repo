"""Self-contained HTML report: body map, mole table with crops, and (when
comparing two scans) a change summary."""

import base64
import html
import os

DISCLAIMER = (
    "MoleMapper is a personal tracking tool, not a medical device. It cannot "
    "diagnose skin cancer, and it can miss or mis-measure moles. Any mole that "
    "is new, growing, changing shape or colour, bleeding, or itching should be "
    "shown to a dermatologist regardless of what this report says."
)

_CSS = """
body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; margin: 2rem auto;
       max-width: 1100px; padding: 0 1rem; color: #222; background: #fafafa; }
h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 2rem; }
.disclaimer { background: #fff3cd; border: 1px solid #ffe08a; border-radius: 8px;
              padding: .8rem 1rem; font-size: .9rem; }
table { border-collapse: collapse; width: 100%; font-size: .85rem; background: #fff; }
th, td { border: 1px solid #ddd; padding: .4rem .6rem; text-align: left; }
th { background: #f0f0f0; }
img.crop { image-rendering: pixelated; max-height: 72px; border-radius: 4px; }
.map { background: #fff; border: 1px solid #ddd; border-radius: 8px; }
.flag { color: #b00020; font-weight: 600; }
.status-new { color: #b26a00; font-weight: 600; }
.status-missing { color: #666; font-weight: 600; }
.status-stable { color: #2e7d32; }
.status-changed { color: #b00020; font-weight: 700; }
.note { color: #555; font-size: .85rem; }
"""


def _img_b64(path: str) -> str | None:
    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def _body_map_svg(moles: list[dict], highlight: dict[int, str] | None = None) -> str:
    """Unwrapped cylinder map: x = surface angle 0..360, y = height 0..1.
    Think of it as the skin peeled open flat — 0/360 is where the spin began."""
    width, height, pad = 900, 420, 40
    highlight = highlight or {}
    parts = [
        f'<svg class="map" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    ]
    for angle in range(0, 361, 45):
        x = pad + (width - 2 * pad) * angle / 360
        parts.append(
            f'<line x1="{x:.0f}" y1="{pad}" x2="{x:.0f}" y2="{height - pad}" stroke="#eee"/>'
            f'<text x="{x:.0f}" y="{height - pad + 18}" font-size="11" text-anchor="middle" fill="#888">{angle}&#176;</text>'
        )
    parts.append(
        f'<text x="{pad}" y="{pad - 14}" font-size="11" fill="#888">top of body</text>'
        f'<text x="{pad}" y="{height - pad + 32}" font-size="11" fill="#888">angle around the body (unwrapped)</text>'
    )
    colors = {"new": "#e65100", "changed": "#b00020", "missing": "#9e9e9e"}
    for m in moles:
        x = pad + (width - 2 * pad) * (m["angle_deg"] / 360.0)
        y = pad + (height - 2 * pad) * m["height_norm"]
        r = max(3.0, min(10.0, m["diameter_px"] / 3.0))
        status = highlight.get(m["id"], "")
        fill = colors.get(status, "#4a2c17")
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="0.8"/>'
            f'<text x="{x + r + 3:.1f}" y="{y + 4:.1f}" font-size="11" fill="#333">#{m["id"]}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _mole_rows(scan: dict, scan_dir: str) -> str:
    rows = []
    for m in scan["moles"]:
        b64 = _img_b64(os.path.join(scan_dir, m.get("crop", "")))
        img = f'<img class="crop" src="data:image/png;base64,{b64}">' if b64 else "&mdash;"
        rows.append(
            f"<tr><td>#{m['id']}</td><td>{img}</td><td>{m['angle_deg']:.0f}&#176;</td>"
            f"<td>{m['height_norm']:.2f}</td><td>{m['diameter_px']:.1f}</td>"
            f"<td>{html.escape(m['shape'])}</td><td>{m['circularity']:.2f}</td>"
            f"<td>{m['asymmetry']:.2f}</td><td>{m['border_irregularity']:.2f}</td>"
            f"<td>{m['color_variegation']:.1f}</td><td>{m['n_observations']}</td></tr>"
        )
    return "".join(rows)


_TABLE_HEADER = (
    "<tr><th>Mole</th><th>View</th><th>Angle</th><th>Height</th><th>Diameter (px)</th>"
    "<th>Shape</th><th>Circularity</th><th>Asymmetry</th><th>Border irreg.</th>"
    "<th>Color var.</th><th>Seen in frames</th></tr>"
)


def write_scan_report(scan: dict, scan_dir: str, out_path: str | None = None) -> str:
    out_path = out_path or os.path.join(scan_dir, "report.html")
    body = f"""
<h1>MoleMapper scan &mdash; {html.escape(str(scan['date']))}</h1>
<p class="disclaimer">{DISCLAIMER}</p>
<p><b>{scan['mole_count']} moles</b> found from {scan['n_frames_used']} frames
({scan['n_raw_detections']} raw detections before deduplication).</p>
<h2>Body map</h2>
<p class="note">The skin surface unwrapped flat: left-to-right is the angle around the
body as she spins, top-to-bottom matches top-to-bottom of the visible skin.</p>
{_body_map_svg(scan['moles'])}
<h2>All moles</h2>
<table>{_TABLE_HEADER}{_mole_rows(scan, scan_dir)}</table>
"""
    _write(out_path, f"Mole scan {scan['date']}", body)
    return out_path


def write_comparison_report(
    comparison: dict, old_scan: dict, new_scan: dict, old_dir: str, new_dir: str, out_path: str
) -> str:
    changes = comparison["changes"]
    flagged = [c for c in changes if c["status"] in ("changed", "new")]
    highlight = {}
    for c in changes:
        if c["new_id"] is not None and c["status"] in ("new", "changed"):
            highlight[c["new_id"]] = c["status"]

    rows = []
    order = {"changed": 0, "new": 1, "missing": 2, "stable": 3}
    for c in sorted(changes, key=lambda c: order[c["status"]]):
        m = c["new"] or c["old"]
        scan_dir = new_dir if c["new"] else old_dir
        b64 = _img_b64(os.path.join(scan_dir, m.get("crop", "")))
        img = f'<img class="crop" src="data:image/png;base64,{b64}">' if b64 else "&mdash;"
        ids = f"#{c['old_id']} &rarr; #{c['new_id']}" if c["old_id"] and c["new_id"] else (
            f"#{c['new_id']} (new)" if c["new_id"] else f"#{c['old_id']} (old)"
        )
        old_d = f"{c['old']['diameter_px']:.1f}" if c["old"] else "&mdash;"
        new_d = f"{c['new']['diameter_px']:.1f}" if c["new"] else "&mdash;"
        flags = "<br>".join(html.escape(f) for f in c["flags"]) or "&mdash;"
        flag_cls = "flag" if c["status"] == "changed" else "note"
        rows.append(
            f'<tr><td class="status-{c["status"]}">{c["status"]}</td><td>{ids}</td><td>{img}</td>'
            f"<td>{m['angle_deg']:.0f}&#176; / {m['height_norm']:.2f}</td>"
            f'<td>{old_d} &rarr; {new_d}</td><td class="{flag_cls}">{flags}</td></tr>'
        )

    summary = (
        f"<p><b>{comparison['old_count']}</b> moles on {comparison['old_date']} &rarr; "
        f"<b>{comparison['new_count']}</b> on {comparison['new_date']}; "
        f"{comparison['matched']} matched, "
        f"<b>{sum(1 for c in changes if c['status'] == 'changed')} changed</b>, "
        f"{sum(1 for c in changes if c['status'] == 'new')} new, "
        f"{sum(1 for c in changes if c['status'] == 'missing')} missing.</p>"
    )
    attention = ""
    if flagged:
        attention = (
            '<p class="flag">Moles worth a closer look: '
            + ", ".join(f"#{c['new_id']}" for c in flagged if c["new_id"])
            + " &mdash; consider showing these to a dermatologist.</p>"
        )

    body = f"""
<h1>MoleMapper comparison &mdash; {html.escape(str(comparison['old_date']))} vs {html.escape(str(comparison['new_date']))}</h1>
<p class="disclaimer">{DISCLAIMER}</p>
{summary}{attention}
<p class="note">Sizes are compared after a global scale correction of
&times;{comparison['size_scale_correction']} to compensate for different camera distances.</p>
<h2>Current body map (orange = new, red = changed)</h2>
{_body_map_svg(new_scan['moles'], highlight)}
<h2>Change details</h2>
<table><tr><th>Status</th><th>Mole</th><th>View</th><th>Angle / height</th>
<th>Diameter old &rarr; new (px)</th><th>Notes</th></tr>{''.join(rows)}</table>
"""
    _write(out_path, "Mole comparison", body)
    return out_path


def _write(out_path: str, title: str, body: str) -> None:
    doc = (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write(doc)
