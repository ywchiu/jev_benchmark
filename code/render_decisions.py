"""Render results/charts/decisions{,-zh}-{light,dark}.svg from results/per_system/*/board_100.json.

Grouped bars for three of the four decision fields (route, scope_action, boundary), one group per system,
ordered by four-field decision accuracy.

usage: python3 code/render_decisions.py   (run from the repository root)
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYSTEMS = [  # (per_system directory, label lines under the group)
    ("gemma_redesigned", ["Gemma 4 31B"]),
    ("cygnet_gemma31b_redesigned", ["Cygnet", "readout · 31B"]),
    ("jev_redesigned", ["Jev 1.13.0"]),
    ("cygnet_redesigned", ["Cygnet", "(12B)"]),
    ("clef_redesigned", ["Clef", "(27B)"]),
    ("djev_redesigned", ["djev-spark"]),
    ("clef_flash_redesigned", ["Clef-flash", "(9B)"]),
    ("semif_redesigned", ["SemIf"]),
    ("laya_redesigned", ["Laya 322M"]),
]
FIELDS = ["route", "scope_action", "boundary"]
TEXT = {
    "en": dict(axis="Percentage (%)", legend=["Where to look (route)", "Subject change", "Restriction state"]),
    "zh": dict(axis="百分比 (%)", legend=["去哪裡找", "話題是否換了", "之後的限制"]),
}
THEMES = {
    "light": dict(bg="#fcfcfb", text="#0b0b0b", sub="#52514e", grid="#e2e1dc", frame="#9a9992",
                  series=["#2a78d6", "#eb6834", "#1baf7a"]),
    "dark": dict(bg="#1a1a19", text="#ffffff", sub="#c3c2b7", grid="#33322f", frame="#6b6a64",
                 series=["#3987e5", "#d95926", "#199e70"]),
}
W, H = 1180, 470
PX0, PX1, PY0, PY1 = 84, 1150, 30, 334          # plot frame
BAR, GAP = 26, 2


def text_width(s, size):
    return sum(size if ord(ch) > 0x2E7F else size * 0.56 for ch in s)


def rows():
    out = []
    for key, label in SYSTEMS:
        b = json.loads((ROOT / "results/per_system" / key / "board_100.json").read_text())
        out.append(dict(label=label, joint=b["all100_decision_joint_accuracy"],
                        vals=[b[f"all100_{f}_accuracy"] * 100 for f in FIELDS]))
    return sorted(out, key=lambda r: -r["joint"])


def render(lang, theme, data):
    c, t = THEMES[theme], TEXT[lang]
    y_of = lambda v: PY1 - (PY1 - PY0) * v / 100
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>']
    for v in range(0, 101, 20):
        y = y_of(v)
        s.append(f'<line x1="{PX0}" y1="{y:.1f}" x2="{PX1}" y2="{y:.1f}" stroke="{c["grid"]}" stroke-width="1" '
                 'stroke-dasharray="3 3"/>')
        s.append(f'<text x="{PX0 - 12}" y="{y + 4:.1f}" font-size="12.5" fill="{c["sub"]}" text-anchor="end">{v}</text>')
    s.append(f'<rect x="{PX0}" y="{PY0}" width="{PX1 - PX0}" height="{PY1 - PY0}" fill="none" '
             f'stroke="{c["frame"]}" stroke-width="1"/>')
    s.append(f'<text transform="translate(26,{(PY0 + PY1) // 2}) rotate(-90)" font-size="13" fill="{c["text"]}" '
             f'text-anchor="middle">{t["axis"]}</text>')
    group = (PX1 - PX0) / len(data)
    for i, r in enumerate(data):
        cx = PX0 + group * (i + 0.5)
        x = cx - (3 * BAR + 2 * GAP) / 2
        for j, v in enumerate(r["vals"]):
            bx = x + j * (BAR + GAP)
            y = y_of(v)
            s.append(f'<rect x="{bx:.1f}" y="{y:.1f}" width="{BAR}" height="{PY1 - y:.1f}" fill="{c["series"][j]}"/>')
            s.append(f'<text x="{bx + BAR / 2:.1f}" y="{y - 6:.1f}" font-size="10.5" fill="{c["sub"]}" '
                     f'text-anchor="middle">{v:.0f}</text>')
        for k, line in enumerate(r["label"]):
            s.append(f'<text x="{cx:.1f}" y="{PY1 + 24 + 16 * k}" font-size="13" fill="{c["text"]}" '
                     f'text-anchor="middle">{line}</text>')
    # legend, centred under the plot
    items = [(c["series"][j], name, text_width(name, 12.5)) for j, name in enumerate(t["legend"])]
    inner = sum(20 + w for _, _, w in items) + 28 * (len(items) - 1)
    box_w = inner + 28
    bx = (PX0 + PX1) / 2 - box_w / 2
    ly = PY1 + 64
    s.append(f'<rect x="{bx:.1f}" y="{ly}" width="{box_w:.1f}" height="34" rx="3" fill="none" '
             f'stroke="{c["frame"]}" stroke-width="1"/>')
    x = bx + 14
    for color, name, w in items:
        s.append(f'<rect x="{x:.1f}" y="{ly + 10}" width="13" height="13" fill="{color}"/>')
        s.append(f'<text x="{x + 20:.1f}" y="{ly + 21}" font-size="12.5" fill="{c["text"]}">{name}</text>')
        x += 20 + w + 28
    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    data = rows()
    for lang in TEXT:
        for theme in THEMES:
            name = "decisions" + ("-zh" if lang == "zh" else "") + f"-{theme}.svg"
            (ROOT / "results/charts" / name).write_text(render(lang, theme, data))
    for r in data:
        print(" ".join(r["label"]).ljust(22), [round(v) for v in r["vals"]])
