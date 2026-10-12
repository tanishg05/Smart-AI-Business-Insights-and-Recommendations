"""SVG diagram builders for the project guide (pure Python, no dependencies)."""
from html import escape

INK, QUIET, EDGE, GRID = '#0F172A', '#475569', '#94A3B8', '#E2E8F0'
ACCENT, ACCENT_SOFT = '#0284C7', '#E0F2FE'
GREEN, AMBER, RED = '#059669', '#D97706', '#DC2626'
LANE_FILL = '#F8FAFC'


def _t(x, y, text, size=12, weight=400, fill=INK, anchor='start', family=None):
    fam = f" font-family='{family}'" if family else ''
    return (f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{weight}' fill='{fill}' "
            f"text-anchor='{anchor}'{fam}>{escape(text)}</text>")


def _marker(mid, color=EDGE):
    return (f"<marker id='{mid}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
            f"orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill='{color}'/></marker>")


def box(x, y, w, h, title, lines=(), accent=False, mono_title=False, fill='#FFFFFF'):
    stroke = ACCENT if accent else EDGE
    bg = ACCENT_SOFT if accent else fill
    out = [f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{bg}' stroke='{stroke}' "
           f"stroke-width='{2 if accent else 1.2}'/>"]
    out.append(_t(x + w / 2, y + 20, title, 12.5, 650, INK, 'middle', 'JetBrains Mono, Menlo, monospace' if mono_title else None))
    for i, line in enumerate(lines):
        out.append(_t(x + w / 2, y + 37 + i * 14, line, 10.5, 400, QUIET, 'middle'))
    return ''.join(out)


def sequence(title, lanes, steps, width=1000, lane_gap=None, note_rows=()):
    """lanes: [(key, label, sublabel)]; steps: [(from, to, label, kind)] kind in solid|dashed|self|alt."""
    n = len(lanes)
    margin = 70
    gap = lane_gap or (width - 2 * margin) / (n - 1)
    xs = {k: margin + i * gap for i, (k, _, _) in enumerate(lanes)}
    top, row = 64, 34
    height = top + 46 + row * len(steps) + 30
    out = [f"<svg viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='{escape(title)}'>",
           f"<defs>{_marker('sq-arrow')}{_marker('sq-arrow-acc', ACCENT)}{_marker('sq-arrow-red', RED)}</defs>",
           _t(0, 20, title, 14, 650)]
    for k, label, sub in lanes:
        x = xs[k]
        out.append(f"<rect x='{x - 78}' y='{top - 30}' width='156' height='40' rx='8' fill='{LANE_FILL}' stroke='{EDGE}'/>")
        out.append(_t(x, top - 13, label, 12, 650, INK, 'middle'))
        out.append(_t(x, top + 1, sub, 9.5, 400, QUIET, 'middle', 'JetBrains Mono, Menlo, monospace'))
        out.append(f"<line x1='{x}' y1='{top + 12}' x2='{x}' y2='{height - 14}' stroke='{GRID}' stroke-width='1.5' stroke-dasharray='4 4'/>")
    y = top + 40
    for i, (a, b, label, kind) in enumerate(steps, 1):
        color = ACCENT if kind in ('solid', 'self') else RED if kind == 'alt' else EDGE
        mk = 'sq-arrow-acc' if color == ACCENT else 'sq-arrow-red' if color == RED else 'sq-arrow'
        dash = " stroke-dasharray='5 4'" if kind in ('dashed', 'alt') else ''
        xa, xb = xs[a], xs[b]
        badge = _t(14, y + 4, str(i), 10.5, 700, '#FFFFFF', 'middle')
        out.append(f"<circle cx='14' cy='{y}' r='9' fill='{color}'/>{badge}")
        if kind == 'self' or a == b:
            out.append(f"<path d='M{xa} {y - 8} h34 v16 h-32' fill='none' stroke='{color}' stroke-width='1.4' marker-end='url(#{mk})'/>")
            out.append(_t(xa + 42, y + 4, label, 10.5, 400, INK))
        else:
            out.append(f"<line x1='{xa}' y1='{y}' x2='{xb + (-4 if xb > xa else 4)}' y2='{y}' stroke='{color}' stroke-width='1.4'{dash} marker-end='url(#{mk})'/>")
            mid = (xa + xb) / 2
            out.append(f"<rect x='{mid - len(label) * 2.9 - 6}' y='{y - 17}' width='{len(label) * 5.8 + 12}' height='13' fill='#FFFFFF'/>")
            out.append(_t(mid, y - 7, label, 10.5, 400, INK, 'middle'))
        y += row
    out.append('</svg>')
    return ''.join(out)


def architecture():
    W, H = 1000, 640
    o = [f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Architecture map'>",
         f"<defs>{_marker('ar')}{_marker('ar-acc', ACCENT)}</defs>",
         _t(0, 22, 'The backend computes every number; Groq only puts them into words', 15, 650)]
    # Zones
    zones = [(0, 44, 300, 588, 'BROWSER', 'React 18 + Vite  ·  localhost:3000'),
             (340, 44, 420, 588, 'BACKEND', 'FastAPI + pandas  ·  127.0.0.1:8000'),
             (800, 44, 200, 588, 'OUTSIDE', 'files and services')]
    for x, y, w, h, name, sub in zones:
        o.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='{LANE_FILL}' stroke='{GRID}' stroke-width='1.5'/>")
        o.append(_t(x + 16, y + 24, name, 11, 700, QUIET))
        o.append(_t(x + 16, y + 40, sub, 10, 400, QUIET))
    # Browser column
    o.append(box(16, 100, 268, 70, 'App.jsx  ·  pages/', ['Shell: filters, active view (#hash),', 'six views read ONE payload'], mono_title=True))
    o.append(box(16, 190, 268, 70, 'context/CopilotContext', ['ask(question, chart), drawer state,', 'Groq status · chat kept separate'], mono_title=True))
    o.append(box(16, 280, 268, 70, 'hooks/', ['useDashboardData · useProactiveInsights', 'useCountUp · useMountAnimation'], mono_title=True))
    o.append(box(16, 370, 268, 70, 'services/api.js', ['the only file that talks to the server:', 'axios calls + SSE stream reader'], accent=True, mono_title=True))
    o.append(box(16, 460, 268, 70, 'components/', ['SectionCard (Inspect) · KPIGrid · Heatmap', 'GroqCopilotDrawer · ScenarioSimulator'], mono_title=True))
    o.append(box(16, 550, 268, 62, 'styles/ · utils/', ['tokens.css · chartTheme · formatters'], mono_title=True))
    # Backend column
    o.append(box(356, 100, 388, 70, 'app.py', ['loads backend/.env · CORS · POST /upload', 'startup: DEFAULT_DATASET'], mono_title=True))
    o.append(box(356, 190, 186, 70, 'routes/analytics.py', ['/dashboard · /health', '/api/datasets'], mono_title=True))
    o.append(box(558, 190, 186, 70, 'routes/ai.py', ['/api/ai/query (SSE)', 'insights · scenario'], mono_title=True))
    o.append(box(558, 280, 186, 84, 'GroqService', ['persona + data brief', 'streaming · model fallback', 'error → local engine'], mono_title=True))
    o.append(box(558, 384, 186, 70, 'InsightEngine', ['data brief for Groq', 'rules · offline answers'], mono_title=True))
    o.append(box(356, 384, 172, 84, 'simulation.py', ['lead-time demand model', 'stockout P · lost sales', 'delay curve'], mono_title=True))
    o.append(box(558, 474, 186, 138, 'DataService', ['in-memory DataFrame', 'clean + enrich columns', 'filter mask', 'segment_table()', '~20 aggregations', 'cache per filter set'], accent=True, mono_title=True))
    # Outside column
    o.append(box(816, 474, 168, 84, 'CSV files', ['backend/uploads/', 'fmcg_clean.csv', '186,892 rows'], mono_title=False))
    o.append(box(816, 280, 168, 84, 'Groq API', ['openai/gpt-oss-120b', 'chat completions', 'stream=True'], mono_title=False))
    o.append(box(816, 100, 168, 70, 'backend/.env', ['GROQ_API_KEY (secret)', 'git-ignored'], mono_title=True))
    # Connectors
    def ln(d, acc=False, label=None, lx=0, ly=0, both=False):
        c = ACCENT if acc else EDGE
        m = 'ar-acc' if acc else 'ar'
        s = f"<path d='{d}' fill='none' stroke='{c}' stroke-width='1.5' marker-end='url(#{m})'" + (f" marker-start='url(#{m})'" if both else '') + "/>"
        if label:
            s += f"<rect x='{lx - len(label) * 3 - 5}' y='{ly - 11}' width='{len(label) * 6 + 10}' height='14' rx='3' fill='#FFFFFF'/>" + _t(lx, ly, label, 10, 600, c, 'middle')
        return s
    o.append(ln('M284 405 H320 V225 H356', True, 'HTTP JSON', 320, 318, both=True))
    o.append(ln('M284 395 H330 V140 H356', False))
    o.append(ln('M651 260 V280', True))             # ai.py -> GroqService
    o.append(ln('M651 364 V384', True))             # Groq -> InsightEngine
    o.append(ln('M558 419 H528', False))            # Insight -> simulation
    o.append(ln('M651 454 V474', False))            # Insight -> DataService
    o.append(ln('M744 321 H816', True, 'prompt / stream', 780, 312, both=True))
    o.append(ln('M816 516 H744', False, 'read CSV', 780, 508))
    o.append(ln('M900 170 V200 H760 V215 H744', False, 'key', 800, 196))
    o.append(ln('M449 260 V300 H543 V530 H558', False, 'analytics', 449, 290))  # analytics -> DataService
    o.append('</svg>')
    return ''.join(o)


def pipeline():
    W, H = 1000, 210
    o = [f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Data pipeline'>",
         f"<defs>{_marker('pp')}</defs>", _t(0, 20, 'From a CSV row to a number on screen', 14, 650)]
    steps = [('1  Upload', ['POST /upload', 'saved to uploads/']), ('2  Validate', ['6 required', 'columns present?']),
             ('3  Clean + enrich', ['types, drop bad rows', 'season, revenue, OTIF']),
             ('4  Hold in memory', ['one DataFrame', 'no database']), ('5  Filter', ['boolean mask', 'region/channel/…']),
             ('6  Aggregate', ['~20 functions', 'cached per filter'])]
    w, gap, y = 148, 22, 50
    for i, (t, lines) in enumerate(steps):
        x = i * (w + gap)
        o.append(box(x, y, w, 76, t, lines, accent=(i == 5)))
        if i < len(steps) - 1:
            o.append(f"<path d='M{x + w} {y + 38} H{x + w + gap - 2}' stroke='{EDGE}' stroke-width='1.5' marker-end='url(#pp)'/>")
    o.append(f"<path d='M{5 * (w + gap) + w / 2} {y + 76} V{y + 112} H{w / 2} V{y + 118}' fill='none' stroke='{GRID}' stroke-width='1.5'/>")
    o.append(_t(500, y + 140, 'One JSON payload (KPIs, trend, heatmap, quadrant, deficits…) → every view reads from it', 11.5, 600, ACCENT, 'middle'))
    o.append('</svg>')
    return ''.join(o)


def fallback_tree():
    W, H = 1000, 250
    o = [f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Who answers'>",
         f"<defs>{_marker('ft')}</defs>", _t(0, 20, 'Who answers your question: Groq if it can, the local engine otherwise', 14, 650)]
    o.append(box(0, 96, 170, 60, 'Question arrives', ['POST /api/ai/query']))
    o.append(f"<polygon points='250,126 320,86 390,126 320,166' fill='#FFFFFF' stroke='{EDGE}' stroke-width='1.2'/>")
    o.append(_t(320, 123, 'GROQ_API_KEY', 10.5, 650, INK, 'middle')); o.append(_t(320, 137, 'set?', 10.5, 400, QUIET, 'middle'))
    o.append(f"<polygon points='480,76 560,36 640,76 560,116' fill='#FFFFFF' stroke='{EDGE}' stroke-width='1.2'/>")
    o.append(_t(560, 73, 'Groq call', 10.5, 650, INK, 'middle')); o.append(_t(560, 87, 'succeeds?', 10.5, 400, QUIET, 'middle'))
    o.append(box(760, 30, 240, 56, 'Groq streams the answer', ['source: groq'], accent=True))
    o.append(box(470, 150, 220, 70, 'Call failed', ['404 model gone: retry once on a', 'model the key can use']))
    o.append(box(760, 160, 240, 70, 'Local analytics engine', ['offline_answer(): same 4 sections,', 'note shows Groq\'s exact error']))
    for d in ['M170 126 H250', 'M390 126 H430 V76 H480', 'M640 76 H760', 'M580 116 V150', 'M690 170 H725 V66 H760', 'M690 200 H760', 'M320 166 V240 H880 V230']:
        o.append(f"<path d='{d}' fill='none' stroke='{EDGE}' stroke-width='1.4' marker-end='url(#ft)'/>")
    for x, y, t in [(420, 70, 'yes'), (700, 70, 'yes'), (600, 138, 'no'), (724, 216, 'still fails'), (600, 236, 'no key'), (760, 120, 'retry works')]:
        o.append(f"<rect x='{x - len(t) * 3 - 3}' y='{y - 10}' width='{len(t) * 6 + 6}' height='13' fill='#FFFFFF'/>" + _t(x, y, t, 10, 600, QUIET, 'middle'))
    o.append('</svg>')
    return ''.join(o)
