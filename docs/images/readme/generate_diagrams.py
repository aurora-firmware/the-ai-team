"""Generate the README diagrams as self-contained, animated SVGs in the Aurora Firmware style.

Run from the repository root:

    uv run --no-project --with fonttools --with brotli python docs/images/readme/generate_diagrams.py

Keep the diagram text in step with ai-process/ (workflow_overview.md, quality_gates.md,
escalation_procedure.md) and regenerate after a change.

Style: the Aurora Firmware brand palette (Dark Blue, Orange, Red and the red-to-orange
45-degree gradient) and its typefaces, Bruno Ace for titles and agent names and Josefin
Sans for everything else. GitHub renders README images through <img>, which cannot load
web fonts, so each SVG embeds a subset of the fonts holding only the glyphs it uses.
The subsets are modified versions under the SIL Open Font License (fonts/OFL-*.txt), so
they are registered under neutral family names ("AF Display", "AF Sans") and carry no
name table, which keeps clear of Josefin Sans's Reserved Font Name.

Colour carries meaning, not identity: every agent card looks the same (Dark Blue card,
Orange role name); Orange and the gradient mark the Product Owner's decisions, Info Blue
marks automated gates, Red marks FAIL and regressions, Orange Light marks escalation,
and Success Green marks PASS and integrated work.
"""

import base64
import io
import sys
from functools import cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
FONTS = HERE / "fonts"
BRUNO = FONTS / "BrunoAce-Regular.ttf"
JOSEFIN = FONTS / "JosefinSans-wght.ttf"

# Aurora Firmware palette (corporate image manual). GRAY is the palette's status gray,
# used for secondary text because Text Gray (#6B7080) is too dark on Dark Blue.
BG, PANEL, CARD, EDGE = "#080A24", "#0F1340", "#1A1E4A", "#2E3372"
ORANGE, ORANGE_L, RED, RED_L = "#F7941D", "#FABA6A", "#E63B26", "#F4695A"
GREEN, BLUE, GRAY, WHITE, BODY = "#22C55E", "#3B82F6", "#9CA3AF", "#FFFFFF", "#D8DAE8"
MARKERS = {"g": GRAY, "r": RED_L, "ok": GREEN, "o": ORANGE_L, "y": ORANGE, "b": BLUE}

# text classes: (font key, size, letter-spacing)
TEXT = {
    "title": ("bruno", 28, 0), "role": ("bruno", 13, 0.3), "num": ("bruno", 21, 0),
    "sub": ("jos400", 18, 0), "ph": ("jos600", 19, 0), "h": ("jos600", 16, 0),
    "t": ("jos400", 14.5, 0), "s": ("jos400", 14, 0), "cap": ("jos400", 11.5, 1.5),
}
FONT_FILE = {"bruno": (BRUNO, None), "jos400": (JOSEFIN, 400), "jos600": (JOSEFIN, 600)}
FAMILY = {"bruno": ("AF Display", 400), "jos400": ("AF Sans", 400), "jos600": ("AF Sans", 600)}

used = {k: set() for k in FONT_FILE}
overflows = []


@cache
def load(key):
    path, wght = FONT_FILE[key]
    font = TTFont(path)
    return instancer.instantiateVariableFont(font, {"wght": wght}) if wght else font


def width(s, cls):
    key, size, ls = TEXT[cls]
    font = load(key)
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    units = sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else 0.9 * upm for c in s)
    return units * size / upm + ls * (len(s) - 1)


def base_cls(cls):
    return next((c for c in cls.split() if c in TEXT), None)


def txt(x, y, s, cls="t", anchor="middle", fill=None, extra="", wrap=None):
    key = base_cls(cls)
    if key and "mono" not in cls:
        used[TEXT[key][0]].update(c for c in s if c != "→")
    f = f' fill="{fill}"' if fill else ""
    body = escape(s).replace("→", '<tspan class="sys">→</tspan>')
    t = f'<text xml:space="preserve" class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{f}{extra}>{body}</text>'
    return f'<g class="n {wrap}">{t}</g>' if wrap else t


def fits(s, cls, room, where):
    key = base_cls(cls)
    if key and "mono" not in cls and width(s, key) > room:
        overflows.append(f"{where}: {s!r} is {width(s, key):.0f}px, room {room:.0f}px")


# card kinds: stroke, dash, top bar, first-line class, first-line colour
KINDS = {
    "agent": (EDGE, False, ORANGE, "role", ORANGE),      # an agent role
    "step": (EDGE, False, ORANGE, "h", WHITE),           # work an agent does
    "human": (ORANGE, False, None, "h", WHITE),          # the Product Owner's work
    "po": (ORANGE, False, None, "role", WHITE),          # the Product Owner
    "gate_po": ("url(#brand)", False, None, "h", WHITE),  # Gate 1 and Gate 5
    "gate_auto": (BLUE, True, None, "h", WHITE),         # Gates 2 to 4
    "pass": (GREEN, False, None, "h", WHITE),
    "fail": (RED, False, None, "h", WHITE),
    "esc": (ORANGE_L, True, None, "role", ORANGE),
    "neutral": (EDGE, False, None, "h", WHITE),
    "ghost": (GRAY, True, None, "t", BODY),
}


def card(x, y, w, h, kind, l1, l2=None, d="", l1cls=None, l2cls="s", l2fill=None):
    stroke, dashed, bar, cls1, fill1 = KINDS[kind]
    cls1 = l1cls or cls1
    cx = x + w / 2
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    sw = 2 if kind == "gate_po" else 1.5
    out = [f'<g class="n {d}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{CARD}" stroke="{stroke}" stroke-width="{sw}"{dash}/>']
    if bar:
        out.append(f'<rect x="{x + 14}" y="{y}" width="{w - 28}" height="2.5" rx="1" fill="{bar}"/>')
    fits(l1, cls1, w - 14, l1)
    if l2 is None:
        out.append(txt(cx, y + h / 2 + 5, l1, cls1, fill=fill1))
    else:
        fits(l2, l2cls, w - 14, l1)
        out.append(txt(cx, y + h / 2 - 3, l1, cls1, fill=fill1))
        out.append(txt(cx, y + h / 2 + 15, l2, l2cls, fill=l2fill))
    out.append("</g>")
    return "\n".join(out)


def arrow(d, color="g", d_cls="", flow=False, dashed=False, width_=1.6):
    c = MARKERS[color]
    extra = ' class="flow"' if flow else (' stroke-dasharray="5 4"' if dashed else "")
    return (f'<g class="e {d_cls}"><path d="{d}" fill="none" stroke="{c}" stroke-width="{width_}" '
            f'marker-end="url(#m-{color})"{extra}/></g>')


def panel(x, y, w, h, head, sub, d=""):
    return (f'<g class="n {d}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.5"/>'
            + txt(x + w / 2, y + 32, head, "ph") + txt(x + w / 2, y + 52, sub, "s") + "</g>")


def band(x, y, w, h, label, lx, d=""):
    """The dashed blue frame around the automated part of a diagram."""
    return (f'<g class="n {d}"><rect class="ants" x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{PANEL}" '
            f'stroke="{BLUE}" stroke-opacity=".55" stroke-width="1.5"/>'
            + txt(lx, y + 26, label, "s", extra=' letter-spacing=".6"') + "</g>")


def font_face(key):
    path, wght = FONT_FILE[key]
    family, weight = FAMILY[key]
    font = TTFont(path)
    if wght:
        font = instancer.instantiateVariableFont(font, {"wght": wght})
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(used[key])) + " ")
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"      @font-face {{ font-family: '{family}'; font-weight: {weight}; src: url(data:font/woff2;base64,{data}) format('woff2'); }}"


STYLE = f"""
      .title {{ font-family: 'AF Display', sans-serif; font-size: {TEXT['title'][1]}px; fill: {WHITE}; }}
      .role  {{ font-family: 'AF Display', sans-serif; font-size: {TEXT['role'][1]}px; letter-spacing: .3px; }}
      .num   {{ font-family: 'AF Display', sans-serif; font-size: {TEXT['num'][1]}px; fill: {WHITE}; }}
      .sub   {{ font-size: {TEXT['sub'][1]}px; fill: {GRAY}; }}
      .ph    {{ font-weight: 600; font-size: {TEXT['ph'][1]}px; fill: {WHITE}; }}
      .h     {{ font-weight: 600; font-size: {TEXT['h'][1]}px; fill: {WHITE}; }}
      .t     {{ font-size: {TEXT['t'][1]}px; fill: {BODY}; }}
      .s     {{ font-size: {TEXT['s'][1]}px; fill: {GRAY}; }}
      .cap   {{ font-size: {TEXT['cap'][1]}px; letter-spacing: 1.5px; }}
      .mono  {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; letter-spacing: 0; }}
      .sys   {{ font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}

      .n {{ opacity: 0; transform: translateY(8px); animation: rise .45s cubic-bezier(.2,.8,.3,1) forwards; }}
      .e {{ opacity: 0; animation: f .4s ease forwards; }}
      .flow {{ stroke-dasharray: 6 6; animation: flow 1.2s linear infinite; }}
      .ants {{ stroke-dasharray: 8 6; animation: flow 2.4s linear infinite; }}
      .pulse {{ animation: pulse 2.4s ease-in-out infinite; }}
      .d1{{animation-delay:.1s}} .d2{{animation-delay:.3s}} .d3{{animation-delay:.5s}} .d4{{animation-delay:.7s}}
      .d5{{animation-delay:.9s}} .d6{{animation-delay:1.1s}} .d7{{animation-delay:1.3s}} .d8{{animation-delay:1.5s}}
      .d9{{animation-delay:1.7s}} .d10{{animation-delay:1.9s}} .d11{{animation-delay:2.1s}} .d12{{animation-delay:2.3s}}

      @keyframes f {{ to {{ opacity: 1; }} }}
      @keyframes rise {{ to {{ opacity: 1; transform: translateY(0); }} }}
      @keyframes flow {{ to {{ stroke-dashoffset: -24; }} }}
      @keyframes pulse {{ 0%,100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}

      @media (prefers-reduced-motion: reduce) {{
        .n, .e {{ opacity: 1 !important; animation: none !important; transform: none !important; }}
        .flow, .ants, .pulse {{ animation: none !important; }}
      }}"""

TOP = 24  # the title block is taller than the content coordinates assume


def svg(w, h, title, sub, body):
    head = ('<g class="n d1">' + txt(w // 2, 54, title, "title")
            + f'<rect x="{w // 2 - 70}" y="70" width="140" height="3" rx="1.5" fill="url(#brand)"/>'
            + txt(w // 2, 100, sub, "sub") + "</g>")
    faces = "\n".join(font_face(k) for k in FONT_FILE if used[k])
    marks = "".join(
        f'<marker id="m-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for k, c in MARKERS.items()
    )
    H = h + TOP
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" font-family="'AF Sans', sans-serif">
  <defs>
    <linearGradient id="brand" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{RED}"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>
    {marks}
    <style><![CDATA[
{faces}
{STYLE}
    ]]></style>
  </defs>
  <rect x="1" y="1" width="{w - 2}" height="{H - 2}" rx="18" fill="{BG}" stroke="{EDGE}" stroke-width="1.5"/>
  {head}
  <g transform="translate(0 {TOP})">
{body}
  </g>
</svg>
'''


def gate_circle(cx, cy, label, n, human, d, r=32):
    stroke = "url(#brand)" if human else BLUE
    ring = (f'<circle class="pulse" cx="{cx}" cy="{cy}" r="{r + 7}" fill="none" stroke="{ORANGE}" stroke-opacity=".5" stroke-width="1.5"/>'
            if human else "")
    return (f'<g class="n {d}"><circle cx="{cx}" cy="{cy}" r="{r}" fill="{CARD}" stroke="{stroke}" stroke-width="{3 if human else 2}"/>{ring}'
            + (txt(cx, cy - 7, label, "cap", fill=ORANGE_L if human else BLUE) if label else "")
            + txt(cx, cy + (15 if label else 7), n, "num") + "</g>")


# ---------------------------------------------------------------- 00 two gates
def two_gates():
    b, cy = [], 216
    b.append(card(16, cy - 32, 146, 64, "po", "Product Owner", "feature request", "d2"))
    for cx, n, cap, d in ((222, "1", "approve spec", "d3"), (931, "5", "approve merge", "d9")):
        b.append(gate_circle(cx, cy, "GATE", n, True, d))
        b.append(txt(cx, cy + 92, cap, "s", wrap=d))
    b.append(band(282, cy - 82, 608, 152, "AUTONOMOUS  ·  agents stop and ask only when the rules say they must", 586, "d4"))
    chips = [("Planner", "spec + tasks", GRAY), ("Architect", "design · Gate 2", BLUE), ("Developer", "builds · TDD", GRAY),
             ("Reviewer", "Gate 3", BLUE), ("Integration", "Gate 4", BLUE)]
    x, cw, gap = 295, 110, 8
    for i, (name, cap, capcol) in enumerate(chips):
        d = f"d{5 + i // 2}"
        b.append(card(x, cy - 28, cw, 56, "agent", name, None, d))
        b.append(txt(x + cw / 2, cy + 52, cap, "s", fill=capcol, wrap=d))
        if i < 4:
            b.append(arrow(f"M{x + cw + 1},{cy} H{x + cw + gap - 1}", "g", "d6"))
        x += cw + gap
    b.append(card(983, cy - 32, 121, 64, "pass", "main", "tested · reviewed", "d10", l1cls="h mono"))
    b.append(arrow(f"M163,{cy} H187", "g", "d3"))
    b.append(arrow(f"M262,{cy} H280", "g", "d4"))
    b.append(arrow(f"M891,{cy} H897", "g", "d9"))
    b.append(arrow(f"M971,{cy} H981", "ok", "d10"))
    b.append(txt(560, 346, "Blocked work escalates:  Developer / Reviewer / Integrator  →  Architect  →  Product Owner", "s", wrap="d11"))
    return svg(1120, 376, "You approve twice. The agents do the rest.",
               "Two product-owner gates. Everything between them runs on its own.", "\n".join(b))


# ------------------------------------------------------------ 01 process overview
def process_overview():
    b = []
    b.append(panel(30, 110, 380, 540, "Spec + planning", "shaped with the Product Owner", "d1"))
    b.append(panel(440, 110, 350, 540, "Development loop", "/dev-loop · runs on its own", "d1"))
    b.append(panel(820, 110, 270, 220, "Final sign-off", "when the task queue is empty", "d1"))
    b.append(panel(820, 350, 270, 300, "Bug loop", "/bug-loop · diagnosis first", "d1"))

    # panel A
    steps = [("Feature request", "Product Owner", "human"), ("Brainstorm → spec", "Planner with the Product Owner", "step"),
             ("Gate 1", "Product Owner approves the spec", "gate_po"), ("Feature architecture", "Architect · ADRs", "step"),
             ("Task breakdown", "Planner · atomic tasks", "step"), ("Gate 2", "Architect preflights the task plan", "gate_auto")]
    y = 180
    for i, (l1, l2, kind) in enumerate(steps):
        b.append(card(48, y, 230, 46, kind, l1, l2, f"d{2 + i}"))
        if i < 5:
            b.append(arrow(f"M163,{y + 47} V{y + 72}", "g", f"d{3 + i}"))
        y += 74
    b.append(card(286, 254, 118, 46, "ghost", "change-request", "skips Gate 1", "d3"))
    b.append(arrow("M345,301 V425 H282", "g", "d5", dashed=True))
    b.append(arrow("M279,573 H425 V203 H507", "g", "d8"))

    # panel B
    bsteps = [(180, "neutral", "Next pending task", "from the local tracker", None),
              (270, "agent", "Developer", "implements · TDD", None),
              (360, "agent", "Reviewer", "Gate 3 · two-stage review", BLUE),
              (450, "pass", "Integration", "Gate 4 · merge + full test suite", BLUE)]
    for i, (y, kind, l1, l2, l2fill) in enumerate(bsteps):
        b.append(card(510, y, 210, 46, kind, l1, l2, f"d{8 + i}", l2fill=l2fill))
        if i < 3:
            b.append(arrow(f"M615,{y + 47} V{y + 86}", "ok" if i == 2 else "g", f"d{9 + i}"))
    b.append(txt(628, 437, "PASS", "s", anchor="start", fill=GREEN, wrap="d11"))
    b.append(arrow("M509,383 H486 V293 H507", "r", "d11", flow=True))
    b.append(f'<g class="n d11"><text class="s" x="476" y="338" text-anchor="middle" fill="{RED_L}" transform="rotate(-90 476 338)">FAIL</text></g>')
    used["jos400"].update("FAIL")
    b.append(arrow("M721,463 H752 V213 H723", "g", "d12", flow=True))
    b.append(f'<g class="n d12"><text class="s" x="766" y="338" text-anchor="middle" transform="rotate(-90 766 338)">next task</text></g>')
    used["jos400"].update("next task")
    b.append(txt(615, 548, "Stops on: empty queue · blocked task · escalation", "s", wrap="d12"))
    b.append(txt(615, 568, "Up to 3 review cycles, then the Architect is consulted", "s", wrap="d12"))

    b.append(arrow("M721,190 H850", "g", "d12"))
    b.append(txt(727, 182, "queue empty", "s", anchor="start", wrap="d12"))
    b.append(arrow("M721,485 H800 V437 H850", "r", "d12"))
    b.append(txt(727, 503, "regression", "s", anchor="start", fill=RED_L, wrap="d12"))

    # sign-off
    b.append(card(853, 176, 204, 36, "step", "Spec-truth check · Architect", None, "d10", l1cls="t"))
    b.append(arrow("M955,213 V224", "g", "d10"))
    b.append(card(853, 226, 204, 36, "neutral", "Status report", None, "d11", l1cls="t"))
    b.append(arrow("M955,263 V274", "g", "d11"))
    b.append(card(853, 276, 204, 44, "gate_po", "Gate 5 · Product Owner", "approves dev-agent → main", "d12"))

    # bug loop
    bugs = [(420, "diagnose", "step"), (470, "fix", "step"), (520, "review", "step"), (570, "integrate", "pass")]
    for i, (y, l1, kind) in enumerate(bugs):
        b.append(card(853, y, 204, 34, kind, l1, None, f"d{9 + i}", l1cls="t"))
        if i < 3:
            b.append(arrow(f"M955,{y + 35} V{y + 48}", "g", f"d{10 + i}"))
    b.append(arrow("M852,537 H838 V487 H850", "r", "d12", flow=True))
    b.append(f'<g class="n d12"><text class="s" x="831" y="512" text-anchor="middle" fill="{RED_L}" transform="rotate(-90 831 512)">FAIL</text></g>')
    b.append(txt(955, 630, "resolved bugs join the Gate 5 summary", "s", wrap="d12"))
    return svg(1120, 680, "From feature request to main",
               "Three phases and five gates. The Product Owner owns Gate 1 and Gate 5; agents run the rest.", "\n".join(b))


# --------------------------------------------------------------- 02 review cycle
def review_cycle():
    b = []
    b.append(card(40, 170, 160, 90, "neutral", "Pending task", "local tracker", "d2"))
    b.append(card(240, 170, 200, 90, "agent", "Developer", "task branch · TDD", "d3"))
    b.append(card(480, 170, 200, 90, "agent", "Reviewer", "Gate 3 · two-stage review", "d4", l2fill=BLUE))
    b.append(card(715, 170, 210, 90, "pass", "Integration", "Gate 4 · merge into dev-agent", "d5", l2fill=BLUE))
    b.append(card(960, 170, 120, 90, "pass", "completed", "tests pass", "d6", l1cls="h mono"))
    b.append(arrow("M201,215 H237", "g", "d3"))
    b.append(arrow("M441,215 H477", "g", "d4"))
    b.append(arrow("M681,215 H712", "ok", "d5"))
    b.append(txt(697, 206, "PASS", "s", fill=GREEN, wrap="d5"))
    b.append(arrow("M926,215 H957", "ok", "d6"))
    b.append(arrow("M580,169 C580,108 340,108 340,166", "r", "d7", flow=True, width_=2))
    b.append(txt(460, 112, "FAIL · the Developer answers every finding", "t", fill=RED_L, wrap="d7"))
    b.append(arrow("M580,261 V327", "o", "d8"))
    b.append(txt(588, 300, "ESCALATE, or a 3rd FAIL", "s", anchor="start", fill=ORANGE_L, wrap="d8"))
    b.append(card(480, 330, 200, 56, "esc", "Architect", "guidance, or Product Owner", "d8"))
    b.append(arrow("M820,261 V327", "r", "d9"))
    b.append(txt(828, 300, "regression", "s", anchor="start", fill=RED_L, wrap="d9"))
    b.append(card(720, 330, 200, 56, "fail", "Open bug", "→ /bug-loop", "d9"))
    b.append(txt(560, 430, "The loop takes the next pending task until the queue is empty, a task is blocked, or escalation is needed.", "s", wrap="d10"))
    return svg(1120, 460, "Every task earns its merge",
               "Developer → Reviewer → integration, repeated until the Reviewer passes the work.", "\n".join(b))


# ----------------------------------------------------------------- 03 escalation
def escalation():
    b = []
    b.append(card(60, 230, 300, 90, "step", "1 · Role self-recovery", "retries within its own threshold", "d2"))
    b.append(card(410, 170, 300, 90, "step", "2 · Architect consultation", "one attempt · escalation-review", "d4"))
    b.append(card(760, 110, 300, 90, "gate_po", "3 · Product Owner", "decides the next action", "d6"))
    b.append(arrow("M361,262 H385 V215 H407", "o", "d3"))
    b.append(txt(393, 284, "threshold", "s", anchor="start", fill=ORANGE_L, wrap="d3"))
    b.append(txt(393, 299, "exceeded", "s", anchor="start", fill=ORANGE_L, wrap="d3"))
    b.append(arrow("M711,202 H735 V155 H757", "o", "d5"))
    b.append(txt(743, 224, "not", "s", anchor="start", fill=ORANGE_L, wrap="d5"))
    b.append(txt(743, 239, "resolved", "s", anchor="start", fill=ORANGE_L, wrap="d5"))
    b.append(arrow("M560,261 C560,360 220,370 210,324", "ok", "d7", flow=True))
    b.append(txt(400, 368, "resolved → the role continues", "t", fill=GREEN, wrap="d7"))
    b.append(txt(560, 412, "Thresholds:  Developer, 3 failed attempts  |  Reviewer, ESCALATE or 3 review cycles  |  Integrator, 1 merge attempt", "s", wrap="d8"))
    return svg(1120, 440, "Blocked work climbs a short ladder",
               "Self-recovery first, then one Architect consultation, then the Product Owner decides.", "\n".join(b))


# ------------------------------------------------------------------ 04 init stamp
def init_stamp():
    b = []
    b.append(panel(30, 110, 390, 380, "This repository", "the framework", "d1"))
    comps = [("Team definition", "ai-process/ rules · agent + skill sources"),
             ("Generators", "agents, skills, layout, AGENTS.md, templates"),
             ("CLI", "ai-team · install, create, validate, move"),
             ("End-user docs", "cli/docs/ · guides/")]
    for i, (l1, l2) in enumerate(comps):
        b.append(card(50, 180 + i * 74, 350, 60, "neutral", l1, l2, f"d{2 + i}"))
    b.append(arrow("M421,300 H458", "g", "d6"))
    b.append(f'<g class="n d6"><rect x="460" y="274" width="200" height="52" rx="26" fill="{CARD}" stroke="url(#brand)" stroke-width="2.5"/>'
             + txt(560, 306, "$ ai-team init .", "h mono", fill=WHITE) + "</g>")
    b.append(arrow("M661,300 H712", "y", "d7", flow=True))
    for off, op in ((24, .35), (12, .6)):
        b.append(f'<g class="n d7"><rect x="{720 + off}" y="{130 - off}" width="350" height="330" rx="14" fill="{PANEL}" stroke="{EDGE}" opacity="{op}"/></g>')
    b.append(f'<g class="n d8"><rect x="720" y="130" width="350" height="330" rx="14" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.5"/>'
             + txt(895, 162, "your project", "ph") + txt(895, 182, "any repository, any stack", "s") + "</g>")
    rows = [(".claude/agents/", "role agents", ORANGE), (".claude/skills/", "procedures (skills)", ORANGE),
            ("ai-team/", "specs · decisions · docs", BLUE), (".ai-team.toml", "framework config", GRAY),
            ("AGENTS.md", "starter guidance (optional)", ORANGE_L), (".ai-team/tracker/", "tasks · bugs · CRs", GRAY)]
    for i, (path, what, col) in enumerate(rows):
        y = 216 + i * 40
        fits(what, "s", 1052 - 754 - 10 - len(path) * 8.2, path)  # monospace path is about 8.2px a character
        b.append(f'<g class="n d{8 + i // 2}"><rect x="740" y="{y - 16}" width="4" height="22" rx="2" fill="{col}"/>'
                 + txt(754, y, path, "t mono", anchor="start", fill=WHITE) + txt(1052, y, what, "s", anchor="end") + "</g>")
    b.append(txt(560, 518, "ai-process/ stays here: it is the spec the exported agents and skills implement.", "s", wrap="d12"))
    return svg(1120, 545, "One command installs the team",
               "ai-team init writes the agents, skills and project skeleton into any repository.", "\n".join(b))


# -------------------------------------------------------------- 05 spec vs impl
def spec_impl():
    b = []
    b.append(panel(40, 110, 440, 230, "ai-process/", "specification layer · the single source of truth", "d2"))
    for i, (l1, l2) in enumerate((("Workflows", "processes/"), ("Standards", "guidelines/"), ("Structure", "architecture/"))):
        y = 180 + i * 50
        b.append(f'<g class="n d{3 + i}"><rect x="60" y="{y}" width="400" height="40" rx="8" fill="{CARD}" stroke="{ORANGE}" stroke-opacity=".8" stroke-width="1.5"/>'
                 + txt(78, y + 25, l1, "h", anchor="start") + txt(442, y + 25, l2, "t mono", anchor="end") + "</g>")
    b.append(panel(640, 110, 440, 230, "cli/src/ai_team/init/sources/", "implementation layer · exported by ai-team init", "d6"))
    for i, (l1, l2) in enumerate((("Agents", "agents/*.md"), ("Skills", "skills/<name>/SKILL.md"), ("Project skeleton", "project/ · root/"))):
        y = 180 + i * 50
        b.append(f'<g class="n d{7 + i}"><rect x="660" y="{y}" width="400" height="40" rx="8" fill="{CARD}" stroke="{EDGE}" stroke-width="1.5"/>'
                 + txt(678, y + 25, l1, "h", anchor="start") + txt(1042, y + 25, l2, "t mono", anchor="end") + "</g>")
    b.append(arrow("M482,200 H636", "y", "d6", flow=True, width_=2))
    b.append(txt(560, 190, "dictates", "t", fill=ORANGE, wrap="d6"))
    b.append(arrow("M638,260 H486", "g", "d10", dashed=True))
    b.append(txt(560, 284, "checked against", "s", wrap="d10"))
    b.append(txt(560, 380, "Change a rule in ai-process/ first, then update the agents and skills that implement it. Never let them contradict each other.", "s", wrap="d11"))
    return svg(1120, 410, "Rules first, implementation second",
               "ai-process/ decides. Agents and skills carry it out faithfully.", "\n".join(b))


# ---------------------------------------------------------------- 06 quality gates
def quality_gates():
    b = []
    b.append(band(270, 120, 600, 210, "AUTOMATED  ·  inside planning and the loops", 570, "d2"))
    b.append(f'<g class="e d2"><line x1="40" y1="230" x2="1076" y2="230" stroke="{EDGE}" stroke-width="2" marker-end="url(#m-g)"/></g>')
    b.append(txt(40, 262, "feature request", "s", anchor="start", wrap="d2"))
    b.append(txt(1080, 262, "main", "s mono", anchor="end", wrap="d2"))
    gates = [("Spec approval", "Product Owner", "approved spec", True),
             ("Task plan preflight", "Architect", "ready task queue", False),
             ("Code review", "Reviewer", "PASS · FAIL · ESCALATE", False),
             ("Integration tests", "Integration procedure", "merged, tests pass", False),
             ("Final sign-off", "Product Owner", "dev-agent → main", True)]
    for i, (name, owner, out, human) in enumerate(gates):
        cx, d = 180 + i * 195, f"d{3 + i}"
        b.append(txt(cx, 182, name, "h", wrap=d))
        b.append(gate_circle(cx, 230, None, str(i + 1), human, d))
        b.append(txt(cx, 290, owner, "t", fill=ORANGE if human else BLUE, wrap=d))
        b.append(txt(cx, 308, out, "s", wrap=d))
    return svg(1120, 360, "Five gates between an idea and main",
               "The Product Owner decides at Gate 1 and Gate 5. Gates 2 to 4 run without them.", "\n".join(b))


FILES = {
    "00_two_gates.svg": two_gates, "01_process_overview.svg": process_overview,
    "02_review_cycle.svg": review_cycle, "03_escalation.svg": escalation, "04_init_stamp.svg": init_stamp,
    "05_spec_vs_impl.svg": spec_impl, "06_quality_gates.svg": quality_gates,
}
for name, fn in FILES.items():
    for chars in used.values():
        chars.clear()
    (OUT / name).write_text(fn())
    print(f"{name}  {(OUT / name).stat().st_size // 1024} KB")
if overflows:
    sys.exit("text overflows its card:\n  " + "\n  ".join(overflows))
