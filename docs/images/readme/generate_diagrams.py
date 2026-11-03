"""Generate the README diagrams as self-contained animated SVGs.

Run from the repository root:  python docs/images/readme/generate_diagrams.py
Keep the diagram text in step with ai-process/ (workflow_overview.md,
quality_gates.md, escalation_procedure.md) and regenerate after a change.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
STYLE = """\
      .bg    { fill: #0B1120; stroke: #1E293B; stroke-width: 1.5; }
      .panel { fill: #0F172A; stroke: #1E293B; stroke-width: 1.5; }
      .title { font-weight: 700; font-size: 28px; fill: #F8FAFC; letter-spacing: -0.4px; }
      .sub   { font-size: 15px; fill: #94A3B8; }
      .ph    { font-weight: 700; font-size: 17px; fill: #F8FAFC; }
      .h     { font-weight: 700; font-size: 14px; fill: #F8FAFC; }
      .t     { font-size: 12px; fill: #CBD5E1; }
      .s     { font-size: 12px; fill: #94A3B8; }
      .mono  { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
      .card  { fill: #111827; stroke-width: 1.6; }
      .ln    { fill: none; stroke: #64748B; stroke-width: 1.6; }

      .n { opacity: 0; transform: translateY(8px); animation: rise .45s cubic-bezier(.2,.8,.3,1) forwards; }
      .e { opacity: 0; animation: f .4s ease forwards; }
      .flow { stroke-dasharray: 6 6; animation: flow 1.2s linear infinite; }
      .ants { stroke-dasharray: 8 6; animation: flow 2.4s linear infinite; }
      .pulse { animation: pulse 2.4s ease-in-out infinite; }
      .d1{animation-delay:.1s} .d2{animation-delay:.3s} .d3{animation-delay:.5s} .d4{animation-delay:.7s}
      .d5{animation-delay:.9s} .d6{animation-delay:1.1s} .d7{animation-delay:1.3s} .d8{animation-delay:1.5s}
      .d9{animation-delay:1.7s} .d10{animation-delay:1.9s} .d11{animation-delay:2.1s} .d12{animation-delay:2.3s}

      @keyframes f { to { opacity: 1; } }
      @keyframes rise { to { opacity: 1; transform: translateY(0); } }
      @keyframes flow { to { stroke-dashoffset: -24; } }
      @keyframes pulse { 0%,100% { opacity: .55; } 50% { opacity: 1; } }

      @media (prefers-reduced-motion: reduce) {
        .n, .e { opacity: 1 !important; animation: none !important; transform: none !important; }
        .flow, .ants, .pulse { animation: none !important; }
      }
"""

PO, PLAN, ARCH, DEV, REV, INT = "#FACC15", "#A78BFA", "#60A5FA", "#22D3EE", "#F472B6", "#34D399"
FAIL, ESC, GRAY = "#F87171", "#FB923C", "#64748B"
MARKERS = {"g": GRAY, "r": FAIL, "ok": INT, "o": ESC, "y": PO, "b": ARCH, "v": PLAN, "c": DEV}


def tint(hex_color, a=0.10):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    bg = (17, 24, 39)
    return "#%02X%02X%02X" % tuple(round(c * a + k * (1 - a)) for c, k in zip((r, g, b), bg))


def svg(w, h, title, sub, body):
    marks = "".join(
        f'<marker id="m-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for k, c in MARKERS.items()
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Inter, 'Segoe UI', system-ui, -apple-system, sans-serif">
  <defs>
    {marks}
    <style><![CDATA[
{STYLE}    ]]></style>
  </defs>
  <rect class="bg" x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18"/>
  <g class="n d1"><text class="title" x="{w // 2}" y="52" text-anchor="middle">{escape(title)}</text>
  <text class="sub" x="{w // 2}" y="80" text-anchor="middle">{escape(sub)}</text></g>
{body}
</svg>
'''


def txt(x, y, s, cls="t", anchor="middle", fill=None, extra="", wrap=None):
    f = f' fill="{fill}"' if fill else ""
    t = f'<text xml:space="preserve" class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{f}{extra}>{escape(s)}</text>'
    return f'<g class="n {wrap}">{t}</g>' if wrap else t


def card(x, y, w, h, color, l1, l2=None, d="", dashed=False, l1cls="h", mono2=False):
    """A role card: tinted fill, colored border, one or two centered lines."""
    cx = x + w / 2
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    out = [f'<g class="n {d}">',
           f'<rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="10" stroke="{color}" fill="{tint(color)}"{dash}/>']
    if l2 is None:
        out.append(txt(cx, y + h / 2 + 5, l1, l1cls))
    else:
        out.append(txt(cx, y + h / 2 - 3, l1, l1cls))
        out.append(txt(cx, y + h / 2 + 14, l2, "t mono" if mono2 else "t"))
    out.append("</g>")
    return "\n".join(out)


def arrow(d, color="g", d_cls="", flow=False, dashed=False, width=1.6):
    c = MARKERS[color]
    extra = ' class="flow"' if flow else (' stroke-dasharray="5 4"' if dashed else "")
    return (f'<g class="e {d_cls}"><path d="{d}" fill="none" stroke="{c}" stroke-width="{width}" '
            f'marker-end="url(#m-{color})"{extra}/></g>')


def panel(x, y, w, h, head, sub, d=""):
    return (f'<g class="n {d}"><rect class="panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="14"/>'
            + txt(x + w / 2, y + 30, head, "ph") + txt(x + w / 2, y + 49, sub, "s") + "</g>")


# ---------------------------------------------------------------- 00 two gates
def two_gates():
    b = []
    b.append(card(30, 190, 140, 60, PO, "Product Owner", "feature request", "d2"))
    for cx, n, cap, d in ((235, "1", "approve spec", "d3"), (890, "5", "approve merge", "d9")):
        b.append(f'<g class="n {d}"><circle cx="{cx}" cy="220" r="32" fill="{tint(PO, .16)}" stroke="{PO}" stroke-width="2"/>'
                 f'<circle class="pulse" cx="{cx}" cy="220" r="38" fill="none" stroke="{PO}" stroke-opacity=".45" stroke-width="1.5"/>'
                 + txt(cx, 215, "GATE", "s", fill=PO) + txt(cx, 234, n, "h", extra=' font-size="18"')
                 + txt(cx, 280, cap, "s") + "</g>")
    b.append('<g class="n d4"><rect x="290" y="140" width="555" height="160" rx="16" fill="#0F172A" stroke="#334155" stroke-width="1.5" class="ants"/>'
             + txt(567, 166, "AUTONOMOUS · agents stop and ask only when the rules say they must", "s", extra=' letter-spacing=".4"') + "</g>")
    chips = [("Planner", "spec + tasks", PLAN), ("Architect", "design · Gate 2", ARCH), ("Developer", "builds · TDD", DEV),
             ("Reviewer", "Gate 3", REV), ("Integration", "Gate 4", INT)]
    x = 305
    for i, (name, cap, col) in enumerate(chips):
        b.append(card(x, 192, 96, 56, col, name, None, f"d{5 + i // 2}"))
        b.append(f'<g class="n d{5 + i // 2}">' + txt(x + 48, 270, cap, "s") + "</g>")
        if i < 4:
            b.append(arrow(f"M{x + 97},220 H{x + 110}", "g", "d6"))
        x += 110
    b.append(card(940, 190, 150, 60, INT, "main", "tested · reviewed", "d10", l1cls="h mono"))
    b.append(arrow("M171,220 H200", "g", "d3"))
    b.append(arrow("M268,220 H288", "g", "d4"))
    b.append(arrow("M846,220 H855", "g", "d9"))
    b.append(arrow("M923,220 H938", "g", "d10"))
    b.append(f'<g class="n d11">' + txt(560, 345, "Blocked work escalates:  Developer / Reviewer / Integrator  →  Architect  →  Product Owner", "s") + "</g>")
    return svg(1120, 380, "You approve twice. The agents do the rest.",
               "Two product-owner gates. Everything between them runs on its own.", "\n".join(b))


# ------------------------------------------------------------ 01 process overview
def process_overview():
    b = []
    b.append(panel(30, 110, 380, 540, "Spec + planning", "shaped with the Product Owner", "d1"))
    b.append(panel(440, 110, 350, 540, "Development loop", "/dev-loop · runs on its own", "d1"))
    b.append(panel(820, 110, 270, 220, "Final sign-off", "when the task queue is empty", "d1"))
    b.append(panel(820, 350, 270, 300, "Bug loop", "/bug-loop · diagnosis first", "d1"))

    # panel A
    steps = [("Feature request", "Product Owner", PO, False), ("Brainstorm → spec", "Planner with the Product Owner", PLAN, False),
             ("Gate 1", "Product Owner approves the spec", PO, True), ("Feature architecture", "Architect · ADRs", ARCH, False),
             ("Task breakdown", "Planner · atomic tasks", PLAN, False), ("Gate 2", "Architect preflights the task plan", ARCH, True)]
    y = 180
    for i, (l1, l2, col, gate) in enumerate(steps):
        b.append(card(48, y, 230, 46, col, l1, l2, f"d{2 + i}", dashed=gate))
        if i < 5:
            b.append(arrow(f"M163,{y + 47} V{y + 72}", "g", f"d{3 + i}"))
        y += 74
    b.append(card(292, 254, 104, 46, GRAY, "change-request", "skips Gate 1", "d3", dashed=True, l1cls="t"))
    b.append(arrow("M344,301 V425 H282", "g", "d5", dashed=True))
    # A -> B
    b.append(arrow("M279,573 H425 V203 H507", "g", "d8"))

    # panel B
    bx, bw = 510, 210
    bsteps = [(180, "Next pending task", "from the local tracker", GRAY), (270, "Developer", "implements · TDD", DEV),
              (360, "Reviewer", "Gate 3 · two-stage review", REV), (450, "Integration", "Gate 4 · merge + full test suite", INT)]
    for i, (y, l1, l2, col) in enumerate(bsteps):
        b.append(card(bx, y, bw, 46, col, l1, l2, f"d{8 + i}"))
        if i < 3:
            b.append(arrow(f"M615,{y + 47} V{y + 86}", "ok" if i == 2 else "g", f"d{9 + i}"))
    b.append(txt(628, 437, "PASS", "s", anchor="start", fill=INT, wrap="d11"))
    b.append(arrow("M509,383 H486 V293 H507", "r", "d11", flow=True))
    b.append(f'<g class="n d11"><text class="s" x="478" y="338" text-anchor="middle" fill="{FAIL}" transform="rotate(-90 478 338)">FAIL</text></g>')
    b.append(arrow("M721,463 H752 V213 H723", "g", "d12", flow=True))
    b.append(f'<g class="n d12"><text class="s" x="766" y="338" text-anchor="middle" transform="rotate(-90 766 338)">next task</text></g>')
    b.append(f'<g class="n d12">' + txt(615, 548, "Stops on: empty queue · blocked task · escalation", "s")
             + txt(615, 568, "Up to 3 review cycles, then the Architect is consulted", "s") + "</g>")

    # B -> sign-off (queue empty) and B -> bug loop (regression)
    b.append(arrow("M721,190 H850", "g", "d12"))
    b.append(txt(726, 182, "queue empty", "s", anchor="start", wrap="d12"))
    b.append(arrow("M721,485 H800 V437 H850", "r", "d12"))
    b.append(txt(726, 503, "regression", "s", anchor="start", fill=FAIL, wrap="d12"))

    # sign-off
    b.append(card(853, 176, 204, 36, ARCH, "Spec-truth check · Architect", None, "d10", l1cls="t"))
    b.append(arrow("M955,213 V224", "g", "d10"))
    b.append(card(853, 226, 204, 36, GRAY, "Status report", None, "d11", l1cls="t"))
    b.append(arrow("M955,263 V274", "g", "d11"))
    b.append(card(853, 276, 204, 44, PO, "Gate 5 · Product Owner", "approves dev-agent → main", "d12", dashed=True))

    # bug loop
    bugs = [(420, "diagnose", DEV), (470, "fix", DEV), (520, "review", REV), (570, "integrate", INT)]
    for i, (y, l1, col) in enumerate(bugs):
        b.append(card(853, y, 204, 34, col, l1, None, f"d{9 + i}", l1cls="t"))
        if i < 3:
            b.append(arrow(f"M955,{y + 35} V{y + 48}", "g", f"d{10 + i}"))
    b.append(arrow("M852,537 H838 V487 H850", "r", "d12", flow=True))
    b.append(f'<g class="n d12"><text class="s" x="832" y="512" text-anchor="middle" fill="{FAIL}" transform="rotate(-90 832 512)">FAIL</text></g>')
    b.append(f'<g class="n d12">' + txt(955, 630, "resolved bugs join the Gate 5 summary", "s") + "</g>")
    return svg(1120, 680, "From feature request to main",
               "Three phases and five gates. The Product Owner owns Gate 1 and Gate 5; agents run the rest.", "\n".join(b))


# --------------------------------------------------------------- 02 review cycle
def review_cycle():
    b = []
    b.append(card(40, 170, 160, 90, GRAY, "Pending task", "local tracker", "d2"))
    b.append(card(240, 170, 200, 90, DEV, "Developer", "task branch · TDD", "d3"))
    b.append(card(480, 170, 200, 90, REV, "Reviewer", "Gate 3 · two-stage review", "d4"))
    b.append(card(720, 170, 200, 90, INT, "Integration", "Gate 4 · merge into dev-agent", "d5"))
    b.append(card(960, 170, 120, 90, INT, "completed", "tests pass", "d6", l1cls="h mono"))
    b.append(arrow("M201,215 H237", "g", "d3"))
    b.append(arrow("M441,215 H477", "g", "d4"))
    b.append(arrow("M681,215 H717", "ok", "d5"))
    b.append(txt(699, 206, "PASS", "s", fill=INT, wrap="d5"))
    b.append(arrow("M921,215 H957", "ok", "d6"))
    b.append(arrow("M580,169 C580,108 340,108 340,166", "r", "d7", flow=True, width=2))
    b.append(txt(460, 112, "FAIL · Developer answers every finding", "t", fill=FAIL, wrap="d7"))
    b.append(arrow("M580,261 V327", "o", "d8"))
    b.append(txt(588, 300, "ESCALATE, or a 3rd FAIL", "s", anchor="start", fill=ESC, wrap="d8"))
    b.append(card(480, 330, 200, 56, ESC, "Architect", "guidance, or Product Owner", "d8"))
    b.append(arrow("M820,261 V327", "r", "d9"))
    b.append(txt(828, 300, "regression", "s", anchor="start", fill=FAIL, wrap="d9"))
    b.append(card(720, 330, 200, 56, FAIL, "Open bug", "→ /bug-loop", "d9", mono2=True))
    b.append(f'<g class="n d10">' + txt(560, 430, "The loop takes the next pending task until the queue is empty, a task is blocked, or escalation is needed.", "s") + "</g>")
    return svg(1120, 460, "Every task earns its merge",
               "Developer → Reviewer → integration, repeated until the Reviewer passes the work.", "\n".join(b))


# ----------------------------------------------------------------- 03 escalation
def escalation():
    b = []
    b.append(card(60, 230, 300, 90, DEV, "1 · Role self-recovery", "retries within its own threshold", "d2"))
    b.append(card(410, 170, 300, 90, ARCH, "2 · Architect consultation", "one attempt · escalation-review", "d4"))
    b.append(card(760, 110, 300, 90, PO, "3 · Product Owner", "decides the next action", "d6"))
    b.append(arrow("M361,262 H385 V215 H407", "o", "d3"))
    b.append(txt(393, 284, "threshold", "s", anchor="start", fill=ESC, wrap="d3"))
    b.append(txt(393, 299, "exceeded", "s", anchor="start", fill=ESC, wrap="d3"))
    b.append(arrow("M711,202 H735 V155 H757", "o", "d5"))
    b.append(txt(743, 224, "not", "s", anchor="start", fill=ESC, wrap="d5"))
    b.append(txt(743, 239, "resolved", "s", anchor="start", fill=ESC, wrap="d5"))
    b.append(arrow("M560,261 C560,360 220,370 210,324", "ok", "d7", flow=True))
    b.append(txt(400, 368, "resolved → the role continues", "t", fill=INT, wrap="d7"))
    b.append(f'<g class="n d8">' + txt(560, 412, "Thresholds:  Developer, 3 failed attempts  |  Reviewer, ESCALATE or 3 review cycles  |  Integrator, 1 merge attempt", "s") + "</g>")
    return svg(1120, 440, "Blocked work climbs a short ladder",
               "Self-recovery first, then one Architect consultation, then the Product Owner decides.", "\n".join(b))


# ------------------------------------------------------------------ 04 init stamp
def init_stamp():
    b = []
    b.append(panel(30, 110, 390, 380, "This repository", "the framework", "d1"))
    comps = [("Team definition", "ai-process/ rules · agent + skill sources", PLAN),
             ("Generators", "agents, skills, layout, AGENTS.md, templates", ARCH),
             ("CLI", "ai-team · install, create, validate, move", DEV),
             ("End-user docs", "cli/docs/ · guides/", GRAY)]
    y = 180
    for i, (l1, l2, col) in enumerate(comps):
        b.append(card(50, y, 350, 60, col, l1, l2, f"d{2 + i}"))
        y += 74
    b.append(arrow("M421,300 H458", "g", "d6"))
    b.append(f'<g class="n d6"><rect x="460" y="274" width="200" height="52" rx="26" fill="{tint(INT, .14)}" stroke="{INT}" stroke-width="1.8"/>'
             + txt(560, 306, "$ ai-team init .", "h mono", fill="#ECFDF5") + "</g>")
    b.append(arrow("M661,300 H712", "ok", "d7", flow=True))
    # stacked ghost repos
    for off, op, d in ((24, .35, "d7"), (12, .6, "d7")):
        b.append(f'<g class="n {d}"><rect x="{720 + off}" y="{130 - off}" width="350" height="330" rx="14" fill="#0F172A" stroke="#334155" opacity="{op}"/></g>')
    b.append(f'<g class="n d8"><rect class="panel" x="720" y="130" width="350" height="330" rx="14"/>'
             + txt(895, 160, "your project", "ph mono") + txt(895, 179, "any repository, any stack", "s") + "</g>")
    rows = [(".claude/agents/", "role agents", PLAN), (".claude/skills/", "procedures (skills)", DEV),
            ("ai-team/", "specs · decisions · docs", ARCH), (".ai-team.toml", "framework config", GRAY),
            ("AGENTS.md", "starter guidance (optional)", PO), (".ai-team/tracker/", "tasks · bugs · CRs, git-ignored", GRAY)]
    y = 214
    for i, (path, what, col) in enumerate(rows):
        b.append(f'<g class="n d{8 + i // 2}"><rect x="740" y="{y - 16}" width="4" height="22" rx="2" fill="{col}"/>'
                 + txt(754, y, path, "t mono", anchor="start", fill="#F8FAFC") + txt(1052, y, what, "s", anchor="end") + "</g>")
        y += 40
    b.append(f'<g class="n d12">' + txt(560, 518, "ai-process/ stays here: it is the spec the exported agents and skills implement.", "s") + "</g>")
    return svg(1120, 545, "One command installs the team",
               "ai-team init writes the agents, skills and project skeleton into any repository.", "\n".join(b))


# -------------------------------------------------------------- 05 spec vs impl
def spec_impl():
    b = []
    b.append(panel(40, 110, 440, 230, "ai-process/", "specification layer · the single source of truth", "d2"))
    for i, (l1, l2) in enumerate((("Workflows", "processes/"), ("Standards", "guidelines/"), ("Structure", "architecture/"))):
        y = 180 + i * 50
        b.append(f'<g class="n d{3 + i}"><rect x="60" y="{y}" width="400" height="40" rx="8" fill="{tint(PO)}" stroke="{PO}" stroke-opacity=".7"/>'
                 + txt(78, y + 25, l1, "h", anchor="start") + txt(442, y + 25, l2, "t mono", anchor="end") + "</g>")
    b.append(panel(640, 110, 440, 230, "cli/src/ai_team/init/sources/", "implementation layer · exported by ai-team init", "d6"))
    for i, (l1, l2, col) in enumerate((("Agents", "agents/*.md", PLAN), ("Skills", "skills/<name>/SKILL.md", DEV),
                                       ("Project skeleton", "project/ · root/", GRAY))):
        y = 180 + i * 50
        b.append(f'<g class="n d{7 + i}"><rect x="660" y="{y}" width="400" height="40" rx="8" fill="{tint(col)}" stroke="{col}" stroke-opacity=".7"/>'
                 + txt(678, y + 25, l1, "h", anchor="start") + txt(1042, y + 25, l2, "t mono", anchor="end") + "</g>")
    b.append(arrow("M482,200 H636", "y", "d6", flow=True, width=2))
    b.append(txt(560, 190, "dictates", "t", fill=PO, wrap="d6"))
    b.append(arrow("M638,260 H486", "g", "d10", dashed=True))
    b.append(txt(560, 284, "checked against", "s", wrap="d10"))
    b.append(f'<g class="n d11">' + txt(560, 380, "Change a rule in ai-process/ first, then update the agents and skills that implement it. Never let them contradict each other.", "s") + "</g>")
    return svg(1120, 410, "Rules first, implementation second",
               "ai-process/ decides. Agents and skills carry it out faithfully.", "\n".join(b))


# ---------------------------------------------------------------- 06 quality gates
def quality_gates():
    b = []
    b.append(f'<g class="n d2"><rect x="270" y="120" width="600" height="210" rx="16" fill="none" stroke="#334155" stroke-width="1.5" class="ants"/>'
             + txt(570, 145, "AUTOMATED · inside planning and the loops", "s", extra=' letter-spacing=".4"') + "</g>")
    b.append(f'<g class="e d2"><line x1="40" y1="230" x2="1076" y2="230" stroke="#334155" stroke-width="2" marker-end="url(#m-g)"/></g>')
    b.append(txt(40, 262, "feature request", "s", anchor="start", wrap="d2"))
    b.append(txt(1080, 262, "main", "s mono", anchor="end", wrap="d2"))
    gates = [("Spec approval", "Product Owner", "approved spec", PO),
             ("Task plan preflight", "Architect", "ready task queue", ARCH),
             ("Code review", "Reviewer", "PASS · FAIL · ESCALATE", REV),
             ("Integration tests", "Integration procedure", "merged, tests pass", INT),
             ("Final sign-off", "Product Owner", "dev-agent → main", PO)]
    for i, (name, owner, out, col) in enumerate(gates):
        cx = 180 + i * 195
        human = col == PO
        ring = (f'<circle class="pulse" cx="{cx}" cy="230" r="40" fill="none" stroke="{col}" stroke-opacity=".45" stroke-width="1.5"/>'
                if human else "")
        b.append(f'<g class="n d{3 + i}">' + txt(cx, 182, name, "h")
                 + f'<circle cx="{cx}" cy="230" r="32" fill="{tint(col, .18)}" stroke="{col}" stroke-width="2"/>{ring}'
                 + txt(cx, 238, str(i + 1), "h", extra=' font-size="22"')
                 + txt(cx, 290, owner, "t", fill=col) + txt(cx, 308, out, "s") + "</g>")
    return svg(1120, 360, "Five gates between an idea and main",
               "The Product Owner decides at Gate 1 and Gate 5. Gates 2 to 4 run without them.", "\n".join(b))


FILES = {
    "00_two_gates.svg": two_gates, "01_process_overview.svg": process_overview,
    "02_review_cycle.svg": review_cycle, "03_escalation.svg": escalation, "04_init_stamp.svg": init_stamp,
    "05_spec_vs_impl.svg": spec_impl, "06_quality_gates.svg": quality_gates,
}
for name, fn in FILES.items():
    (OUT / name).write_text(fn())
    print(name)
