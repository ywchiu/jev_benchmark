"""Render results/charts/leaderboard-{light,dark}.svg from results/per_system/*/board_100.json.

usage: python3 code/render_leaderboard.py   (run from the repository root)
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYSTEMS = [  # (per_system directory, label shown on the chart)
    ("gemma_redesigned", "Gemma 4 31B"),
    ("cygnet_gemma31b_redesigned", "Cygnet readout · 31B"),
    ("jev_redesigned", "Jev 1.13.0"),
    ("cygnet_redesigned", "Cygnet (12B)"),
    ("clef_redesigned", "Clef (27B)"),
    ("djev_redesigned", "djev-spark"),
    ("clef_flash_redesigned", "Clef-flash (9B)"),
    ("semif_redesigned", "SemIf"),
    ("laya_redesigned", "Laya 322M"),
]
THEMES = {
    "light": dict(bg="#fcfcfb", text="#0b0b0b", sub="#52514e", grid="#e6e5e0", tick="#84837c", bar="#2a78d6"),
    "dark": dict(bg="#1a1a19", text="#ffffff", sub="#c3c2b7", grid="#33322f", tick="#84837c", bar="#3987e5"),
}
W, X0, X1, Y0, STEP = 760, 236.0, 698.0, 74, 46


def rows():
    out = []
    for key, label in SYSTEMS:
        b = json.loads((ROOT / "results/per_system" / key / "board_100.json").read_text())
        out.append(dict(label=label, joint=b["all100_decision_joint_accuracy"] * 100,
                        route=b["all100_route_accuracy"] * 100, scope=b["all100_scope_action_accuracy"] * 100,
                        p95=b["latency_ms"]["p95"], reps=b["repeats"]))
    return sorted(out, key=lambda r: -r["joint"])


def render(theme, data):
    c = THEMES[theme]
    n = len(data)
    grid_bottom = Y0 + STEP * (n - 1) + 30
    h = grid_bottom + 62
    scale = (X1 - X0) / 100
    reps = sorted({r["reps"] for r in data})
    rep_text = f"{reps[0]} repeats" if len(reps) == 1 else f"{reps[0]}–{reps[-1]} repeats per system"
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
         'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{h}" fill="{c["bg"]}"/>',
         f'<text x="28" y="34" font-size="15.5" font-weight="600" fill="{c["text"]}">Routing decision accuracy</text>',
         f'<text x="28" y="54" font-size="12" fill="{c["sub"]}">All four decision fields correct &#183; '
         f'100 turns &#215; {rep_text}</text>']
    for pct in range(0, 101, 20):
        x = X0 + pct * scale
        s.append(f'<line x1="{x:.1f}" y1="64" x2="{x:.1f}" y2="{grid_bottom}" stroke="{c["grid"]}" stroke-width="1"/>')
        s.append(f'<text x="{x:.1f}" y="{grid_bottom + 18}" font-size="10.5" fill="{c["tick"]}" '
                 f'text-anchor="middle">{pct}%</text>')
    for i, r in enumerate(data):
        y = Y0 + STEP * i
        w = r["joint"] * scale
        s.append(f'<text x="{X0 - 12:.0f}" y="{y + 13.7:.1f}" font-size="12.5" fill="{c["text"]}" '
                 f'text-anchor="end">{r["label"]}</text>')
        if w > 0:
            s.append(f'<rect x="{X0:.0f}" y="{y}" width="{w:.1f}" height="19" rx="4" fill="{c["bar"]}"/>')
            s.append(f'<rect x="{X0:.0f}" y="{y}" width="4.0" height="19" fill="{c["bar"]}"/>')
        s.append(f'<text x="{X0 + w + 8:.1f}" y="{y + 13.7:.1f}" font-size="12" font-weight="600" '
                 f'fill="{c["text"]}">{r["joint"]:.1f}%</text>')
        s.append(f'<text x="{X0 - 12:.0f}" y="{y + 27.7:.1f}" font-size="10" fill="{c["tick"]}" text-anchor="end">'
                 f'route {r["route"]:.0f}% &#183; scope {r["scope"]:.0f}% &#183; p95 {r["p95"]:.0f}ms</text>')
    s.append(f'<text x="28" y="{h - 14}" font-size="10" fill="{c["tick"]}">Clef, Clef-flash and both Cygnet rows '
             'were added in October 2026; see results/summary.md for how each was served.</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    data = rows()
    for theme in THEMES:
        (ROOT / f"results/charts/leaderboard-{theme}.svg").write_text(render(theme, data))
    for r in data:
        print(f'{r["label"]:<22} {r["joint"]:5.1f}%  reps={r["reps"]}')
