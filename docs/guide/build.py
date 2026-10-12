"""Builds docs/guide/Supply-Chain-Dashboard-Guide.html and renders it to PDF with headless Chrome."""
import subprocess, sys, time, os
from pathlib import Path
from diagrams import architecture, pipeline, fallback_tree, sequence

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / 'Supply-Chain-Dashboard-Guide.html'
OUT_PDF = HERE.parent / 'Supply-Chain-Dashboard-Guide.pdf'

LANES = [('ui', 'React views', 'pages/ · components/'), ('api', 'API client', 'services/api.js'),
         ('route', 'FastAPI route', 'routes/*.py'), ('svc', 'Services', 'services/*.py'), ('ext', 'Outside', 'Groq · disk')]

SEQ_LOAD = sequence('Flow 1 · Opening the dashboard (and every filter change)', LANES, [
    ('ui', 'api', 'fetchDashboard(filters)', 'solid'),
    ('api', 'route', 'GET /dashboard?region=…', 'solid'),
    ('route', 'svc', 'get_dashboard_payload(filters)', 'solid'),
    ('svc', 'svc', 'cache hit? else: mask rows, run ~20 aggregations', 'self'),
    ('svc', 'route', 'payload dict', 'dashed'),
    ('route', 'api', 'JSON (~95 KB, full FMCG)', 'dashed'),
    ('api', 'ui', 'setData → views re-render', 'dashed'),
    ('ui', 'api', 'fetchProactiveInsights()', 'solid'),
    ('api', 'route', 'GET /api/ai/proactive-insights', 'solid'),
    ('route', 'svc', 'rule scan → up to 6 pills', 'solid'),
    ('svc', 'ext', 'Groq rewrites wording (JSON)', 'solid'),
    ('ext', 'svc', 'polished titles / actions', 'dashed'),
    ('svc', 'ui', 'insight pills (numbers unchanged)', 'dashed'),
])

SEQ_ASK = sequence('Flow 2 · Asking the copilot (typed question or Inspect button)', LANES, [
    ('ui', 'ui', 'Inspect click → ask(query, chart data slice ≤ 40 rows)', 'self'),
    ('ui', 'api', 'streamAIQuery({query, filters})', 'solid'),
    ('api', 'route', 'POST /api/ai/query (SSE)', 'solid'),
    ('route', 'svc', 'GroqService.stream_query()', 'solid'),
    ('svc', 'svc', 'build_context(): persona + data brief', 'self'),
    ('svc', 'ext', 'chat.completions(stream=True)', 'solid'),
    ('ext', 'svc', 'token chunks', 'dashed'),
    ('svc', 'route', 'events: meta, delta…, done', 'dashed'),
    ('route', 'api', 'SSE frames: data: {…}', 'dashed'),
    ('api', 'ui', 'append text → drawer only', 'dashed'),
    ('svc', 'svc', 'on error: offline_answer() streams instead', 'alt'),
])

SEQ_SIM = sequence('Flow 3 · Moving a Scenario Lab slider', LANES, [
    ('ui', 'ui', 'slider changes; debounce 180 ms, cancel older request', 'self'),
    ('ui', 'api', 'simulateScenario(params, filters)', 'solid'),
    ('api', 'route', 'POST /api/ai/scenario-simulate', 'solid'),
    ('route', 'svc', 'segment_table() → simulate()', 'solid'),
    ('svc', 'svc', 'baseline vs scenario, regions, delay curve 0–15 d', 'self'),
    ('svc', 'api', 'figures JSON (no LLM involved)', 'dashed'),
    ('api', 'ui', 'tiles count up, charts update', 'dashed'),
    ('ui', 'route', '"Generate briefing" → include_narrative: true', 'solid'),
    ('route', 'ext', 'Groq interprets the computed figures', 'solid'),
    ('ext', 'ui', 'markdown briefing card', 'dashed'),
])

CSS = """
@page { size: A4; margin: 16mm 15mm 18mm; }
* { box-sizing: border-box; }
body { font-family: Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; color: #0F172A; font-size: 10.2pt; line-height: 1.5; margin: 0; }
h1, h2, h3 { letter-spacing: -0.015em; line-height: 1.25; }
h1 { font-size: 26pt; margin: 0 0 6pt; }
h2 { font-size: 16pt; margin: 0 0 8pt; padding-top: 2pt; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 5pt; }
h3 { font-size: 11.5pt; margin: 14pt 0 5pt; }
p { margin: 0 0 7pt; }
code, .mono { font-family: 'JetBrains Mono', Menlo, Consolas, monospace; font-size: 8.8pt; }
code { background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 3px; padding: 0 3px; }
pre { background: #0B0F17; color: #E6EAF2; border-radius: 6px; padding: 9pt 11pt; font-size: 8.6pt; line-height: 1.45; white-space: pre-wrap; margin: 6pt 0 10pt; }
pre code { background: none; border: 0; padding: 0; color: inherit; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0 10pt; font-size: 8.9pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; background: #F1F5F9; color: #334155; font-weight: 600; padding: 5pt 6pt; border-bottom: 1.5px solid #CBD5E1; }
td { padding: 4.5pt 6pt; border-bottom: 1px solid #E2E8F0; vertical-align: top; }
.section { break-before: page; }
.figure { margin: 8pt 0 6pt; page-break-inside: avoid; }
.figure svg { width: 100%; height: auto; display: block; }
.caption { font-size: 8.6pt; color: #475569; margin-top: 3pt; }
.lead { font-size: 11.5pt; color: #1E293B; }
  .callout { break-inside: avoid; border-left: 3px solid #0284C7; background: #F0F9FF; padding: 7pt 10pt; margin: 8pt 0 10pt; border-radius: 0 6px 6px 0; }
.callout.warn { border-color: #D97706; background: #FFFBEB; }
.callout b { display: block; margin-bottom: 2pt; }
.cover { height: 250mm; display: flex; flex-direction: column; }
.cover .eyebrow { font-size: 9pt; letter-spacing: .12em; text-transform: uppercase; color: #0284C7; font-weight: 700; margin-top: 30mm; }
.cover .sub { font-size: 13pt; color: #334155; max-width: 140mm; }
.cover .meta { margin-top: auto; font-size: 9pt; color: #64748B; border-top: 1px solid #E2E8F0; padding-top: 8pt; }
.toc { columns: 2; column-gap: 12mm; margin-top: 14mm; font-size: 10pt; }
.toc div { break-inside: avoid; padding: 3pt 0; border-bottom: 1px dotted #CBD5E1; }
.toc span { color: #0284C7; font-weight: 700; display: inline-block; width: 18pt; }
.formula { font-family: 'Times New Roman', Georgia, serif; font-size: 12pt; text-align: center; margin: 6pt 0 10pt; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; }
.pill { display: inline-block; font-size: 7.5pt; font-weight: 700; padding: 0 5px; border-radius: 3px; letter-spacing: .04em; }
.p-crit { background: #FEE2E2; color: #B91C1C; } .p-warn { background: #FEF3C7; color: #B45309; } .p-opp { background: #E0F2FE; color: #0369A1; }
ol, ul { margin: 0 0 8pt; padding-left: 16pt; } li { margin-bottom: 2.5pt; }
"""

def section(n, title, body):
    return f"<div class='section'><h2>{n}. {title}</h2>{body}</div>"

def fig(svg, caption):
    return f"<div class='figure'>{svg}<div class='caption'>{caption}</div></div>"

TOC = ['What the project does', 'Architecture map', 'File-by-file map', 'Flow: from CSV to dashboard',
       'Flow: asking the copilot', 'Flow: proactive insights', 'Flow: the Scenario Lab',
       'The analytics, explained', 'Frontend internals', 'Lessons from the bugs we fixed',
       'API reference', 'Run, configure, troubleshoot', 'Extend it, and a learning path']

parts = []
parts.append(f"""
<div class='cover'>
  <div class='eyebrow'>Project guide · DVP</div>
  <h1>Supply Chain Intelligence Dashboard</h1>
  <p class='sub'>How it works, where everything lives, and how a request travels from a click in the browser through FastAPI, pandas and Groq and back to the screen.</p>
  <div class='toc'>{''.join(f"<div><span>{i}</span>{t}</div>" for i, t in enumerate(TOC, 1))}</div>
  <div class='meta'>Written for ria · 12 October 2026 · Stack: FastAPI, pandas, NumPy, Groq (openai/gpt-oss-120b), React 18, Vite, Recharts · Reference dataset: fmcg_clean.csv (186,892 rows, Jan 2022 to Dec 2024)</div>
</div>""")

parts.append(section(1, 'What the project does', """
<p class='lead'>The dashboard turns one sales-and-inventory CSV into answers to three questions: what is selling, where stock will run out, and what happens if the supply chain is disrupted.</p>
<p>You load a CSV. The backend cleans it with pandas and computes every metric. The browser draws those metrics as charts. Groq, a hosted large language model, then explains the numbers in plain English. The model never invents the numbers: it only receives ones the backend already computed.</p>
<p>Each CSV row is one sale record. Six columns are required: <code>date</code>, <code>units_sold</code>, <code>price_unit</code>, <code>delivery_days</code>, <code>delivered_qty</code>, <code>stock_available</code>. Optional columns (<code>region</code>, <code>channel</code>, <code>category</code>, <code>sku</code>, <code>promotion_flag</code>) unlock the breakdowns.</p>
<table><tr><th>View</th><th>Question it answers</th><th>What you see</th></tr>
<tr><td><b>Overview</b></td><td>How healthy is the business right now?</td><td>Five KPI cards with deltas and sparklines, revenue trajectory vs moving average, proactive signals, top stock deficits, recommended actions</td></tr>
<tr><td><b>Demand &amp; Sales</b></td><td>Where does revenue come from, and does price move volume?</td><td>Region × channel stacked revenue, channel efficiency matrix, price-elasticity scatter with fitted curve, category bars</td></tr>
<tr><td><b>Operations</b></td><td>Are deliveries late, and which items are short?</td><td>Lead-time histogram with normal curve, lead time by region, stock vs velocity quadrant, replenishment queue</td></tr>
<tr><td><b>Seasonality</b></td><td>When and where does demand peak, and what comes next?</td><td>Season × region heatmap, 7-period forecast with 95% band, seasonal volume and lead time</td></tr>
<tr><td><b>Scenario Lab</b></td><td>What if suppliers slip or demand surges?</td><td>Sliders with live lost sales, stockout probability, fill rate, holding cost, delay curve</td></tr>
<tr><td><b>Intelligence Hub</b></td><td>What should I do about it?</td><td>AI insight pills, one-click prompts, demand split, recommendations</td></tr></table>
<p>Two features run across every view. The <b>Copilot</b> (⌘K or Ctrl+K, or the floating pill) is a chat drawer. The <b>Inspect</b> button on every chart sends that chart's data to the copilot with a tailored question. Four filters (region, channel, category, season) apply to every view and to everything the AI sees.</p>
"""))

parts.append(section(2, 'Architecture map', fig(architecture(), 'Blue boxes are the two files to understand first: <code>services/api.js</code> is the browser\'s only door to the server, and <code>DataService</code> is where every number starts.') + """
<h3>Reading the map, box by box</h3>
<table><tr><th>Part</th><th>What happens there</th></tr>
<tr><td><b>Browser</b></td><td>React draws everything. <code>App.jsx</code> holds the filters and the active view; the views are plain functions of one data object. No business logic lives here: the browser formats and draws.</td></tr>
<tr><td><b>api.js</b></td><td>Every request leaves through this file. It uses axios for normal JSON calls and a small hand-written reader for the copilot's streamed answers.</td></tr>
<tr><td><b>app.py</b></td><td>Starts the server, loads <code>backend/.env</code> (where your Groq key lives), allows the browser's origin (CORS), handles uploads, and can preload a dataset at start-up.</td></tr>
<tr><td><b>routes/</b></td><td>Thin HTTP layer. Each function reads query parameters or a JSON body, calls a service, and turns Python errors into HTTP errors. <code>analytics.py</code> serves the dashboard; <code>ai.py</code> serves the copilot, insights and scenarios.</td></tr>
<tr><td><b>DataService</b></td><td>Owns the dataset: cleaning, filtering, every aggregation and the cache. Everything else asks it for data.</td></tr>
<tr><td><b>InsightEngine</b></td><td>Turns DataService output into words: the dense data brief sent to Groq, the rule-based insight scan, and the offline answers used when Groq is unavailable.</td></tr>
<tr><td><b>simulation.py</b></td><td>The what-if inventory model behind the Scenario Lab. Pure maths, no AI.</td></tr>
<tr><td><b>GroqService</b></td><td>The only file that talks to Groq: builds the prompt, streams the answer, retries on a retired model, and falls back to InsightEngine on any error.</td></tr>
<tr><td><b>Outside</b></td><td>The CSV files on disk, the Groq API on the internet, and the secret key in <code>backend/.env</code>, which git ignores.</td></tr></table>
<div class='callout'><b>The one idea to remember</b>The backend is the single source of truth. The browser never computes a metric, and Groq never computes a number. That is why the dashboard still works with no key: only the wording changes.</div>
"""))

FILES = [
 ('backend/app.py', 69, 'Server entry point: .env loading, CORS, POST /upload with filename sanitising, DEFAULT_DATASET at startup', 'load_default_dataset (43), upload_dataset (57)'),
 ('backend/routes/analytics.py', 92, 'Dashboard and dataset endpoints; legacy /sales, /seasonality…', 'dashboard (25), list_datasets (75), load_dataset (84)'),
 ('backend/routes/ai.py', 81, 'AI endpoints; wraps the copilot stream as Server-Sent Events', 'ai_query (34), proactive_insights (59), scenario_simulate (72)'),
 ('backend/models/schemas.py', 43, 'Pydantic request models; malformed input gets a clear 422', 'AIQueryRequest, ScenarioRequest'),
 ('backend/services/data_service.py', 766, 'Load, clean, filter, aggregate, cache. The heart of the project', '_preprocess (84), filtered (147), _build_payload (199), segment_table (304), _kpis (369), _forecast_series (467)'),
 ('backend/services/insight_engine.py', 472, 'Data brief for Groq, proactive rules, offline answers', 'build_context (44), proactive_insights (101), offline_answer (235)'),
 ('backend/services/simulation.py', 146, 'What-if inventory model', '_evaluate (50), simulate (99)'),
 ('backend/services/groq_service.py', 261, 'Groq client, prompts, streaming, model fallback, error messages', '_create (111), _messages (134), stream_query (149), proactive_insights (200), scenario (235)'),
 ('frontend/src/App.jsx', 189, 'Shell: filters, active view from #hash, loading / empty / error states, error boundary', 'App, Shell, View'),
 ('frontend/src/context/CopilotContext.jsx', 132, 'Copilot state split in two contexts (actions vs chat transcript)', 'CopilotProvider, useCopilot, useCopilotChat'),
 ('frontend/src/services/api.js', 132, 'All HTTP calls; SSE parser for streaming', 'fetchDashboard, streamAIQuery, simulateScenario'),
 ('frontend/src/hooks/', 196, 'Data fetching and small behaviours', 'useDashboardData, useProactiveInsights, useCountUp, useMountAnimation, useHotkey'),
 ('frontend/src/components/', 1415, 'Reusable UI: cards, KPI grid, tooltip, heatmap, drawer, simulator, markdown renderer', 'SectionCard, KPIGrid, GroqCopilotDrawer, ScenarioSimulator'),
 ('frontend/src/pages/', 784, 'The six views', 'DashboardPage, SalesPage, OperationsPage, SeasonalPage, SimulatorPage, AIPage'),
 ('frontend/src/styles/tokens.css + App.css', 903, 'Design system: colours, type, spacing, motion, every component style', 'CSS variables in :root'),
 ('frontend/src/utils/', 130, 'Number formatting and the shared chart theme', 'formatCurrency, formatKpi, COLORS, axisProps'),
]
rows = ''.join(f"<tr><td><code>{f}</code></td><td style='text-align:right'>{n}</td><td>{d}</td><td class='mono' style='font-size:7.8pt'>{k}</td></tr>" for f, n, d, k in FILES)
parts.append(section(3, 'File-by-file map', f"""
<p>About 1,900 lines of Python and 3,900 lines of JavaScript and CSS. Numbers in the last column are line numbers, so you can jump straight to a function in your editor.</p>
<table><tr><th style='width:30%'>File or folder</th><th>Lines</th><th>Responsibility</th><th>Key functions (line)</th></tr>{rows}</table>
<p>Also in the repo: <code>backend/uploads/</code> (CSV files you can load), <code>backend/.env.example</code> (template; the real key goes in <code>backend/.env</code>), <code>docs/research/DET.ipynb</code> (the original exploration notebook), and this guide under <code>docs/</code>.</p>
"""))

parts.append(section(4, 'Flow: from CSV to dashboard', fig(pipeline(), 'Steps 1 to 4 run once per upload; steps 5 and 6 run on every filter change.') + fig(SEQ_LOAD, 'Read top to bottom. Solid arrows are requests, dashed arrows are responses.') + """
<h3>What each step does, in code</h3>
<ol>
<li><b>Upload.</b> <code>POST /upload</code> saves the file under <code>backend/uploads/</code>. The filename is reduced to its last part, so a name like <code>../../app.py</code> cannot escape the folder.</li>
<li><b>Validate.</b> <code>process_upload()</code> rejects the file with a 400 listing any missing required column.</li>
<li><b>Clean and enrich.</b> <code>_preprocess()</code> converts types, drops rows with missing values or non-positive price, and adds: <code>season</code> (from the month), <code>revenue</code> = units × price, <code>on_time</code> (≤ 3 days), <code>in_full</code> (delivered ≥ sold), and <code>segment</code> (SKU · region).</li>
<li><b>Hold in memory.</b> The DataFrame lives on the single <code>data_service</code> object. There is no database: a restart forgets it unless <code>DEFAULT_DATASET</code> is set.</li>
<li><b>Filter.</b> <code>filtered()</code> builds a True/False mask from the query string. <code>channel=Retail,Discount</code> selects both.</li>
<li><b>Aggregate and cache.</b> <code>_build_payload()</code> runs about 20 small functions and stores the result under a key made from the filters, so revisiting a filter is instant. A new upload clears the cache.</li>
</ol>
<div class='callout'><b>Why one big payload?</b>One request gives every view what it needs, so switching views is instant and all charts always agree with each other. Only the copilot, the insight scan and the Scenario Lab make their own requests, because they are slower or interactive.</div>
"""))

parts.append(section(5, 'Flow: asking the copilot', fig(SEQ_ASK, 'The red dashed step is the fallback path: if Groq fails at any point, the local engine streams an answer through the same pipe.') + """
<h3>Context hydration: what Groq actually receives</h3>
<p>The model never sees your CSV. <code>_messages()</code> sends four things:</p>
<ol>
<li><b>Persona</b>: "You are an elite Chief Supply Chain Officer and Quantitative Operations Analyst…", which keeps answers numeric and concrete.</li>
<li><b>Answer format</b>: four required sections (Executive answer, Root cause hypothesis, Tactical actions with dollar impact, Metric citations) and a glossary of velocity, cover and reorder point.</li>
<li><b>Data brief</b> from <code>build_context()</code>: about 15 dense lines with dataset, rows, date range and filters; KPIs; lead time by region, channel and season; the 5 tightest SKU-locations; the seasonality index grid; revenue by channel, region and category; elasticity; quadrant counts; the forecast. For an Inspect click, up to 40 rows of that chart are appended.</li>
<li><b>History</b>: the last 8 exchanges, so follow-ups like "and in the South?" work.</li>
</ol>
<h3>Streaming, step by step</h3>
<p>The route returns <code>text/event-stream</code>. Each event is one line, <code>data: {json}</code>, followed by a blank line. The first event, <code>meta</code>, says who is answering; many <code>delta</code> events carry text; <code>done</code> ends it. In the browser, <code>streamAIQuery()</code> reads the response body chunk by chunk, splits on blank lines, and calls back for each event. The drawer appends the text, which gives the typewriter effect.</p>
""" + fig(fallback_tree(), 'Every path ends in an answer. The note at the top of a fallback answer quotes Groq\'s exact error, for example an expired key.')))

parts.append(section(6, 'Flow: proactive insights', """
<p>Proactive insights run the opposite way to the copilot: Python rules find the problems, and Groq only rewrites the wording. <code>InsightEngine.proactive_insights()</code> checks, on the filtered data:</p>
<table><tr><th>Check</th><th>Rule</th><th>Severity</th></tr>
<tr><td>Stockout hazard</td><td>Any SKU-location below its 95% reorder point, or whose cover is shorter than lead time + 7 days</td><td><span class='pill p-crit'>CRITICAL</span> / <span class='pill p-warn'>WARNING</span></td></tr>
<tr><td>Lead-time anomaly</td><td>Deliveries slower than mean + 2σ</td><td><span class='pill p-crit'>CRITICAL</span> if over 3% of orders</td></tr>
<tr><td>SLA breach</td><td>More than 20% of deliveries beyond the 3-day SLA</td><td><span class='pill p-warn'>WARNING</span></td></tr>
<tr><td>Margin leak</td><td>Promoted orders earn less revenue per order than unpromoted ones</td><td><span class='pill p-warn'>WARNING</span></td></tr>
<tr><td>Seasonal mismatch</td><td>The peak-demand season carries less stock per unit sold than average</td><td><span class='pill p-warn'>WARNING</span> / <span class='pill p-opp'>OPPORTUNITY</span></td></tr>
<tr><td>Channel gap</td><td>Best region × channel earns over 3% more per unit than the worst</td><td><span class='pill p-opp'>OPPORTUNITY</span></td></tr>
<tr><td>Revenue momentum</td><td>Latest 28 days moved 5% or more vs the 28 before</td><td><span class='pill p-warn'>WARNING</span> / <span class='pill p-opp'>OPPORTUNITY</span></td></tr></table>
<p>Hits are sorted by severity, then by estimated dollar impact, and the top 6 are kept. With a key set, <code>GroqService.proactive_insights()</code> asks Groq, in JSON mode, to tighten each title, detail and action while keeping ids, severities and numbers. If that call fails, the rule text is shown unchanged.</p>
<p>On <code>fmcg_clean.csv</code> the scan returns four pills: SLA breach rate 40.2% (PL-South slowest), 47 segments with thin cover, Monsoon under-stocked for its demand (7.07 units of stock per unit sold vs 8.0 average), and promotions that lift units 95%.</p>
"""))

parts.append(section(7, 'Flow: the Scenario Lab', fig(SEQ_SIM, 'The figures come only from the maths below; Groq is involved only if you press Generate briefing.') + """
<h3>The model, in five steps</h3>
<ol>
<li><b>Shift the inputs</b> for every SKU-location: lead time L → (L + delay) × (1 + spike%); demand d → d × (1 + surge%) × (1 + price change)<sup>elasticity</sup>; stock S → S × buffer.</li>
<li><b>Lead-time demand</b> is treated as a normal distribution with mean μ = d·L and spread σ = √(L·σ<sub>d</sub>² + d²·σ<sub>L</sub>²). Both day-to-day demand and the lead time itself vary.</li>
<li><b>Stockout probability</b> is the chance demand exceeds stock: P = 1 − Φ(z), with z = (S − μ) / σ.</li>
<li><b>Units short per cycle</b> use the standard normal loss function below. Multiplying by 30 / L cycles gives lost units over 30 days; × price gives lost sales.</li>
<li><b>Holding cost</b> = stock value × 25% a year × 30/365, so you can see what a bigger buffer costs.</li>
</ol>
<div class='formula'>E[short] = σ · ( φ(z) − z · (1 − Φ(z)) )</div>
<p>On <code>fmcg_clean.csv</code>, adding 8 days of supplier delay moves 30-day lost sales from $119 to $101.5K and fill rate from 100% to 82.5%. The delay curve shows that losses stay near zero for a few days and then climb steeply, which is the shape you would expect when stock covers about 8 days of demand.</p>
"""))

parts.append(section(8, 'The analytics, explained', """
<p>Most numbers come from one idea: treat each <b>segment</b> (one SKU in one region) as a small warehouse, and compare how many days its stock lasts with how long a refill takes.</p>
<table><tr><th>Metric</th><th>How it is computed</th><th>How to read it</th><th>FMCG value</th></tr>
<tr><td>Total revenue</td><td>Σ units_sold × price_unit</td><td>Money in for the filtered range</td><td>$19.95M</td></tr>
<tr><td>Delta</td><td>Last 28 days vs the 28 before (halves for short files)</td><td>Getting better or worse?</td><td>+0.7%</td></tr>
<tr><td>Inventory turnover</td><td>units sold ÷ stock on hand × 365</td><td>Times a year stock sells through</td><td>46.1×/yr</td></tr>
<tr><td>OTIF rate</td><td>Share delivered within 3 days AND delivered ≥ sold</td><td>Service level; 3 days is set by <code>OTIF_SLA_DAYS</code></td><td>59.8%</td></tr>
<tr><td>Velocity</td><td>Average daily units over the segment's last 7 days</td><td>How fast it sells now</td><td>24 to 63 units/day</td></tr>
<tr><td>Cover</td><td>stock ÷ velocity</td><td>Days until empty without a reorder</td><td>6 to 17 days</td></tr>
<tr><td>Need</td><td>average lead time + 7-day review cycle</td><td>Days until a refill could arrive</td><td>about 10 days</td></tr>
<tr><td>Reorder point</td><td>d·L + 1.65 · √(L·σ<sub>d</sub>² + d²·σ<sub>L</sub>²)</td><td>Stock that gives a 95% chance of no stockout</td><td>155 to 348 units</td></tr>
<tr><td>Stockout risk index</td><td>Demand-weighted average of how far cover falls short of need (0–100)</td><td>0 = all covered, 100 = all empty before refill</td><td>8.3</td></tr>
<tr><td>Quadrant</td><td>Velocity and stock split at their medians</td><td>Critical Low, Fast Mover, Overstocked, Dead Stock</td><td>15 / 31 / 14 / 30</td></tr>
<tr><td>Price elasticity</td><td>Slope of log(units) on log(price)</td><td>−1 means +10% price loses about 10% volume</td><td>≈ 0 (synthetic data)</td></tr>
<tr><td>Seasonality index</td><td>Daily units in a season ÷ that region's average</td><td>1.16 = 16% above normal</td><td>Monsoon 1.16</td></tr>
<tr><td>Forecast</td><td>Holt's linear smoothing, band = ±1.96·σ·√h</td><td>Next 7 periods with an honest range</td><td>MAPE 6.3%</td></tr></table>
<div class='callout warn'><b>Assumptions you can change</b>Four constants at the top of <code>data_service.py</code> set the business rules: <code>OTIF_SLA_DAYS = 3</code>, <code>REVIEW_PERIOD_DAYS = 7</code>, <code>SERVICE_Z = 1.65</code> (95% service level) and <code>VELOCITY_WINDOW_DAYS = 7</code>. OTIF is 59.8% only because 40% of FMCG deliveries take 4 or 5 days against the 3-day SLA.</div>
<p>Two details prevent misleading charts. Weekly series drop a final partial week, which otherwise looks like a demand collapse. The fitted elasticity is clamped between −3 and −0.1 inside the simulator so a noisy fit cannot produce absurd demand swings.</p>
"""))

parts.append(section(9, 'Frontend internals', """
<h3>How state flows</h3>
<p><code>App</code> owns the filters. It passes them to <code>useDashboardData</code>, which fetches the payload, and to <code>CopilotProvider</code>, so every AI request carries the current filters. Views receive <code>data</code> as a prop and render; they hold almost no state of their own.</p>
<table><tr><th>Piece</th><th>Job</th><th>Detail worth knowing</th></tr>
<tr><td><code>useDashboardData</code></td><td>Fetch, refetch on filter change, upload, load sample</td><td>Numbers each request and ignores stale replies, so fast filter clicks never show old data. Skeletons appear only on the first load.</td></tr>
<tr><td><code>CopilotContext</code> + <code>CopilotChatContext</code></td><td>Copilot actions vs chat transcript</td><td>Split so streamed tokens re-render only the drawer, not the dashboard.</td></tr>
<tr><td><code>SectionCard</code></td><td>Every card; owns the Inspect button</td><td><code>inspect={{ data, query }}</code> is all a chart needs to get AI help.</td></tr>
<tr><td><code>useMountAnimation</code></td><td>Charts animate once</td><td>Later updates swap in place instead of replaying the draw-in.</td></tr>
<tr><td><code>useCountUp</code></td><td>KPI numbers glide to new values</td><td>Ease-out over 0.9 s; disabled when the OS asks for reduced motion.</td></tr>
<tr><td><code>ErrorBoundary</code></td><td>Contains crashes</td><td>A broken view shows an error card with Try again instead of a blank page.</td></tr>
<tr><td><code>Markdown</code></td><td>Renders copilot answers</td><td>Dependency-free: headings, lists, tables, code, quotes, bold.</td></tr></table>
<h3>The design system</h3>
<p>All styling flows from CSS variables in <code>styles/tokens.css</code>. Surfaces are obsidian (<code>#0B0F17</code>, <code>#111827</code>, <code>#161F30</code>) with 8%-white hairline borders. Four status colours carry meaning: emerald <code>#10B981</code> healthy, amber <code>#F59E0B</code> warning, coral <code>#EF4444</code> critical, ice blue <code>#38BDF8</code> primary. Text uses Inter with −0.015em tracking; every number uses JetBrains Mono with tabular figures so digits line up in columns. One spring curve (<code>--ease-spring</code>) drives hover lifts, view transitions and the drawer. Charts read the same palette from <code>utils/chartTheme.js</code>, and tooltips use a 12px backdrop blur.</p>
<p>Views live in the URL hash (<code>/#operations</code>), so a link opens the right view, and keys 1 to 6 switch between them.</p>
"""))

parts.append(section(10, 'Lessons from the bugs we fixed', """
<p>Four problems came up after the first build. Each one teaches something general, so they are worth understanding.</p>
<table><tr><th>Symptom</th><th>Cause</th><th>Fix</th><th>Lesson</th></tr>
<tr><td>"Connect Groq" stayed on after adding the key</td><td>The key was pasted into <code>backend/.env.example</code>; the app reads <code>backend/.env</code></td><td>Moved the key to <code>.env</code> (git-ignored), restored the template</td><td><code>.example</code> files are committed templates. Secrets go only in ignored files.</td></tr>
<tr><td>"Groq was unreachable (NotFoundError)"</td><td>Groq retired <code>llama-3.3-70b-versatile</code> for this key</td><td>Default <code>openai/gpt-oss-120b</code>; auto-retry on an available model; exact error shown</td><td>Hosted model names change. Ask the API what exists, and surface real error messages.</td></tr>
<tr><td>Page flickered, content vanished</td><td>Every streamed token re-rendered the whole app; Recharts replayed its draw-in on each new data array</td><td>Split the copilot context; animate charts on first mount only</td><td>In React, put fast-changing state where only its consumers subscribe.</td></tr>
<tr><td>"minimumFractionDigits is out of range"</td><td>The tooltip called <code>formatNumber(value, row)</code>, so the data row became the decimal count</td><td>One-argument default formatter; every formatter clamps digits to 0–20</td><td>Be careful passing a two-argument function as a callback; validate inputs at the edge.</td></tr></table>
<p>The flicker fix was measured: while a 2,412-character answer streamed in, chart elements changed 0 times. The tooltip fix was tested by hovering every chart on all six views: 78 tooltips, 0 errors, against 8 errors out of 8 hovers before.</p>
"""))

parts.append(section(11, 'API reference', """
<p>All endpoints run on FastAPI at <code>http://127.0.0.1:8000</code>. While the backend runs, <code>/docs</code> shows interactive documentation where you can try each call.</p>
<table><tr><th>Method</th><th>Path</th><th>Input</th><th>Returns</th></tr>
<tr><td>GET</td><td><code>/health</code></td><td>none</td><td>status, dataset loaded</td></tr>
<tr><td>POST</td><td><code>/upload</code></td><td>multipart CSV</td><td>Full payload for the new file</td></tr>
<tr><td>GET</td><td><code>/api/datasets</code></td><td>none</td><td>CSV files on the server and the active one</td></tr>
<tr><td>POST</td><td><code>/api/datasets/load</code></td><td><code>{file_name}</code></td><td>Loads a file already in uploads/</td></tr>
<tr><td>GET</td><td><code>/dashboard</code></td><td><code>region</code>, <code>channel</code>, <code>category</code>, <code>season</code>, <code>date_from</code>, <code>date_to</code></td><td>Every metric and chart series for that slice</td></tr>
<tr><td>GET</td><td><code>/api/ai/status</code></td><td>none</td><td>Groq on/off, model in use, last error</td></tr>
<tr><td>POST</td><td><code>/api/ai/query</code></td><td><code>{query, context_filters, conversation_history, chart_context, stream}</code></td><td>SSE: meta, delta…, done (JSON if stream is false)</td></tr>
<tr><td>GET</td><td><code>/api/ai/proactive-insights</code></td><td>same filters</td><td>Up to 6 pills: severity, title, detail, metric, action, impact, query</td></tr>
<tr><td>POST</td><td><code>/api/ai/scenario-simulate</code></td><td><code>delay_days</code>, <code>lead_time_spike_pct</code>, <code>demand_shift_pct</code>, <code>safety_stock_multiplier</code>, <code>price_change_pct</code>, <code>price_elasticity_factor</code>, <code>context_filters</code>, <code>include_narrative</code></td><td>Baseline vs scenario, regions, exposed segments, delay curve, optional briefing</td></tr></table>
<p>Older routes (<code>/sales</code>, <code>/seasonality</code>, <code>/operations</code>, <code>/insights</code>, <code>/recommendations</code>) still answer for compatibility; the frontend no longer calls them.</p>
"""))

parts.append(section(12, 'Run, configure, troubleshoot', """
<pre><code># Terminal 1: backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt      # first time only
uvicorn app:app --reload             # http://127.0.0.1:8000

# Terminal 2: frontend
cd frontend
npm install                          # first time only
npm run dev                          # http://localhost:3000</code></pre>
<table><tr><th>Setting (backend/.env)</th><th>Example</th><th>Purpose</th></tr>
<tr><td><code>GROQ_API_KEY</code></td><td><code>gsk_…</code></td><td>Turns on live Groq; empty = local engine. Never commit it.</td></tr>
<tr><td><code>GROQ_MODEL</code></td><td><code>openai/gpt-oss-120b</code></td><td>Model to call; falls back automatically if retired</td></tr>
<tr><td><code>DEFAULT_DATASET</code></td><td><code>fmcg_clean.csv</code></td><td>File in uploads/ loaded at start-up</td></tr>
<tr><td><code>BACKEND_CORS_ORIGINS</code></td><td><code>http://localhost:3000</code></td><td>Browser origins allowed to call the API</td></tr>
<tr><td><code>VITE_API_BASE_URL</code> (frontend/.env)</td><td><code>http://127.0.0.1:8000</code></td><td>Where the frontend finds the API</td></tr></table>
<table><tr><th>Symptom</th><th>Likely cause</th><th>Fix</th></tr>
<tr><td>Copilot says "local engine" after adding a key</td><td>Key in the wrong file, or backend not restarted</td><td>Put it in <code>backend/.env</code>, restart uvicorn, refresh</td></tr>
<tr><td>"Groq call failed (AuthenticationError…)"</td><td>Key wrong or revoked</td><td>Create a new key at console.groq.com/keys</td></tr>
<tr><td>"Can't reach the API at …"</td><td>Backend not running or wrong port</td><td>Start terminal 1; check <code>VITE_API_BASE_URL</code></td></tr>
<tr><td>Dashboard empty after a restart</td><td>Data is held in memory only</td><td>Pick a file on the Connect screen, or set <code>DEFAULT_DATASET</code></td></tr>
<tr><td>Copilot says there is no Monsoon data</td><td><code>test_supply_chain.csv</code> covers 4 days in January</td><td>Load <code>fmcg_clean.csv</code></td></tr>
<tr><td>"This view hit an error"</td><td>A rendering bug in one view</td><td>Try again; the message names the error to report</td></tr></table>
"""))

parts.append(section(13, 'Extend it, and a learning path', """
<p>Every feature follows one route: compute it in a backend service, expose it in the payload or a route, then draw it in a page.</p>
<div class='two'><div>
<h3>Add a KPI card</h3>
<ol><li>In <code>data_service.py</code>, add a dict to the list in <code>_kpis()</code>: <code>key</code>, <code>label</code>, <code>format</code> (currency, percent, turns, index, days), <code>value</code>, <code>delta</code>, <code>status</code>, <code>sparkline</code>.</li>
<li>That's all: <code>KPIGrid</code> renders every item. Adjust <code>.grid--kpi</code> for six columns.</li></ol>
<h3>Add a chart</h3>
<ol><li>Write <code>_my_series(df)</code> and add it to <code>_build_payload()</code>.</li>
<li>In a page: <code>&lt;SectionCard title="…" inspect={{ data: data.my_series }}&gt;</code> around a Recharts chart, using <code>axisProps</code>, <code>gridProps</code>, <code>COLORS</code> and <code>&lt;ChartTooltip rows={…}/&gt;</code>.</li>
<li>Add <code>isAnimationActive={animate}</code> from <code>useMountAnimation()</code> to each series.</li></ol>
</div><div>
<h3>Add an AI feature</h3>
<ol><li>Add a method on <code>GroqService</code> that builds messages with <code>_messages()</code> and calls <code>self._create(…)</code>; the model fallback comes free.</li>
<li>Add a rule-based fallback in <code>InsightEngine</code> so it works without a key.</li>
<li>Expose it in <code>routes/ai.py</code> and call it from <code>api.js</code>.</li></ol>
<h3>Suggested reading order</h3>
<ol><li><code>data_service.py</code>: <code>_preprocess</code>, <code>segment_table</code>, <code>_kpis</code></li>
<li><code>insight_engine.py</code>: <code>build_context</code>, <code>proactive_insights</code></li>
<li><code>groq_service.py</code>: <code>_messages</code>, <code>_create</code>, <code>stream_query</code></li>
<li><code>api.js</code> + <code>CopilotContext.jsx</code>: streaming to screen</li>
<li><code>OperationsPage.jsx</code>: a full view using every building block</li></ol>
</div></div>
<h3>Glossary</h3>
<table><tr><td><b>SKU</b></td><td>One sellable product variant</td><td><b>Lead time</b></td><td>Days from order to delivery</td></tr>
<tr><td><b>Safety stock</b></td><td>Extra stock held against surprises</td><td><b>Fill rate</b></td><td>Share of demand served from stock</td></tr>
<tr><td><b>OTIF</b></td><td>On-time, in-full delivery rate</td><td><b>σ (sigma)</b></td><td>Standard deviation: how spread out values are</td></tr>
<tr><td><b>SSE</b></td><td>Server-Sent Events: a one-way stream from server to browser</td><td><b>LLM</b></td><td>Large language model; Groq hosts them fast</td></tr>
<tr><td><b>CORS</b></td><td>Browser rule for which sites may call an API</td><td><b>Payload</b></td><td>The JSON body of a request or response</td></tr></table>
"""))

html = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Supply Chain Intelligence Dashboard · Project Guide</title><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"
OUT_HTML.write_text(html, encoding='utf-8')
print('wrote', OUT_HTML)

chrome = os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-mac-arm64/chrome-headless-shell')
proc = subprocess.Popen([chrome, '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={OUT_PDF}', OUT_HTML.as_uri()],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    time.sleep(0.5)
    if proc.poll() is not None:
        break
else:
    proc.kill()
print('pdf', OUT_PDF, OUT_PDF.stat().st_size if OUT_PDF.exists() else 'missing')
