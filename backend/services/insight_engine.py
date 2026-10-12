"""Deterministic analytics layer that feeds Groq and stands in for it when no key is set.

- build_context(): serialises the filtered dataset into a dense, token-efficient brief.
- proactive_insights(): rule-based scan for anomalies, stockout hazards, margin leaks and seasonal mismatch.
- offline_answer(): data-grounded markdown answers used when Groq is unavailable.
"""
import json
import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from services.data_service import OTIF_SLA_DAYS, SEASON_ORDER, DataService
from services.simulation import simulate

SEVERITY_RANK = {'CRITICAL': 0, 'WARNING': 1, 'OPPORTUNITY': 2}


def _money(v: float) -> str:
    v = float(v)
    if abs(v) >= 1e6:
        return f'${v / 1e6:,.2f}M'
    if abs(v) >= 1e3:
        return f'${v / 1e3:,.1f}K'
    return f'${v:,.0f}'


def _pct(v: Optional[float], signed: bool = False) -> str:
    if v is None:
        return 'n/a'
    return f'{v * 100:+.1f}%' if signed else f'{v * 100:.1f}%'


class InsightEngine:
    def __init__(self, data: DataService) -> None:
        self.data = data

    # ------------------------------------------------------------------ context hydration

    def snapshot(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.data.get_dashboard_payload(filters)

    def build_context(self, filters: Optional[Dict[str, Any]] = None, chart_context: Optional[Dict[str, Any]] = None) -> str:
        p = self.snapshot(filters)
        if p.get('empty'):
            return f'DATASET {p["file_name"]}: no rows match filters {p["filters"]}.'

        k = {item['key']: item for item in p['kpis']}
        s, lt = p['summary'], p['lead_time']
        lines = [
            f'DATASET {p["file_name"]} | rows {p["rows"]:,} of {p["total_rows"]:,} | '
            f'{p["date_range"]["start"]}→{p["date_range"]["end"]} ({p["date_range"]["days"]}d) | '
            f'filters {json.dumps(p["filters"]) if p["filters"] else "none"}',
            f'KPIS revenue {_money(k["revenue"]["value"])} (last window Δ{_pct(k["revenue"]["delta"], True)} {k["revenue"]["delta_label"]}) | '
            f'units {s["total_sales"]:,.0f} | avg price ${s["avg_price"]:.2f} | turnover {k["turnover"]["value"]:.1f}x/yr | '
            f'OTIF {_pct(k["otif"]["value"])} (SLA {OTIF_SLA_DAYS}d) | stockout risk index {k["stockout_risk"]["value"]:.1f}/100 '
            f'({k["stockout_risk"].get("detail", "")}) | lead {lt["mean"]:.2f}d σ{lt["std"]:.2f} p95 {lt["p95"]:.1f}d',
            'LEAD TIME by region: ' + '; '.join(f'{r["region"]} {r["mean"]:.2f}d σ{r["std"]:.2f}' for r in lt['by_region']),
            'LEAD TIME by channel: ' + '; '.join(f'{r["channel"]} {r["mean"]:.2f}d' for r in lt['by_channel'])
            + ' | by season: ' + '; '.join(f'{k2} {v:.2f}d' for k2, v in lt['by_season'].items())
            + f' | >2σ anomalies (>{lt["anomaly_threshold"]:.1f}d): {lt["anomaly_count"]} | late share {_pct(lt["late_share"])}',
        ]

        if p['deficits']:
            lines.append('TOP DEFICIT SEGMENTS (segment|stock|velocity/d|cover d|need d|reorder pt|gap):')
            for d in p['deficits']:
                lines.append(f'  {d["segment"]}|{d["stock"]:.0f}|{d["velocity"]:.1f}|{d["cover_days"]:.1f}|'
                             f'{d["need_days"]:.1f}|{d["reorder_point"]:.0f}|{d["gap_units"]:.0f}')

        hm = p['heatmap']
        idx = {(c['season'], c['region']): c['index'] for c in hm['cells']}
        lines.append('SEASONALITY INDEX (daily units ÷ region avg): ' + ' | '.join(
            f'{season}: ' + ', '.join(f'{r} {idx.get((season, r), 0):.2f}' for r in hm['regions']) for season in hm['seasons']))

        lines.append('CHANNEL revenue: ' + '; '.join(f'{c["channel"]} {_money(c["revenue"])} ({_pct(c["share"])} units)'
                                                    for c in p['sales_by_channel']))
        lines.append('REGION revenue: ' + '; '.join(f'{c["region"]} {_money(c["revenue"])} ({_pct(c["share"])})'
                                                   for c in p['sales_by_region']))
        lines.append('CATEGORY revenue: ' + '; '.join(f'{c["category"]} {_money(c["revenue"])} @${c["avg_price"]:.2f}'
                                                     for c in p['category_sales']))
        el = p['elasticity']
        if el.get('coefficient') is not None:
            lines.append(f'PRICE ELASTICITY log-log {el["coefficient"]:.3f} (r² {el["r2"]:.3f})')
        vm = p['velocity_matrix']
        lines.append(f'STOCK×VELOCITY quadrants ({vm.get("unit", "segment")}): ' +
                     ', '.join(f'{q} {n}' for q, n in vm.get('counts', {}).items()))
        fc = p['forecast_series']
        if fc.get('forecast'):
            lines.append(f'FORECAST next {len(fc["forecast"])} {p["granularity"]}s (units, 95% band): ' +
                         '; '.join(f'{f["period"]} {f["forecast"]:.0f} [{f["lower"]:.0f}-{f["upper"]:.0f}]' for f in fc['forecast'][:4]) +
                         f' | MAPE {_pct(fc.get("mape"))}')

        if chart_context:
            lines.append(f'FOCUS CHART "{chart_context.get("title", "chart")}": ' +
                         json.dumps(chart_context.get('data', [])[:40], separators=(',', ':'), default=str)[:3000])
        return '\n'.join(lines)

    # ------------------------------------------------------------------ proactive scan

    def proactive_insights(self, filters: Optional[Dict[str, Any]] = None, limit: int = 6) -> List[Dict[str, Any]]:
        p = self.snapshot(filters)
        if p.get('empty'):
            return []
        df = self.data.filtered(filters)
        segments = self.data.segment_table(df)
        lt = p['lead_time']
        out: List[Dict[str, Any]] = []

        # 1. Stockout hazards: stock vs 7-day rolling demand over the replenishment window.
        at_risk = segments[segments['at_risk']]
        thin = segments[segments['cover_days'] < segments['need_days']].sort_values('cover_days')
        if len(at_risk):
            worst = at_risk.sort_values('cover_days').iloc[0]
            exposure = float(((at_risk['need_days'] - at_risk['cover_days']).clip(lower=0) * at_risk['velocity'] * at_risk['price']).sum())
            out.append(self._pill(
                'stockout', 'CRITICAL', f'{len(at_risk)} segments below reorder point',
                f'{worst["segment"]} covers {worst["cover_days"]:.1f} days against a {worst["need_days"]:.1f}-day replenishment need '
                f'(stock {worst["stock_now"]:.0f}, 7-day velocity {worst["velocity"]:.1f}/day).',
                ('Exposure', _money(exposure)), f'Expedite replenishment for {worst["segment"]} and raise its reorder point to {worst["reorder_point"]:.0f} units.',
                exposure, f'Which SKU-locations are below reorder point and how much stock do they need? Start with {worst["segment"]}.'))
        elif len(thin):
            worst = thin.iloc[0]
            exposure = float(((thin['need_days'] - thin['cover_days']).clip(lower=0) * thin['velocity'] * thin['price']).sum())
            out.append(self._pill(
                'stockout', 'WARNING', f'{len(thin)} segments with thin cover',
                f'Stock covers less than lead time + review period. Tightest: {worst["segment"]} at {worst["cover_days"]:.1f} days '
                f'vs {worst["need_days"]:.1f} needed.',
                ('Cover gap', f'{worst["need_days"] - worst["cover_days"]:.1f}d'),
                'Pull forward the next purchase order for these segments.', exposure,
                'Identify SKUs at immediate risk of stockout within 14 days'))

        # 2. Lead-time anomalies (>2σ) and structural lag by region/season.
        if lt['anomaly_count']:
            share = lt['anomaly_count'] / max(p['rows'], 1)
            out.append(self._pill(
                'lead_anomaly', 'CRITICAL' if share > 0.03 else 'WARNING', f'{lt["anomaly_count"]:,} deliveries beyond 2σ',
                f'Deliveries slower than {lt["anomaly_threshold"]:.1f} days ({_pct(share)} of orders). Mean {lt["mean"]:.2f}d, σ {lt["std"]:.2f}.',
                ('Threshold', f'{lt["anomaly_threshold"]:.1f}d'), 'Open a carrier performance review on the lanes driving the tail.',
                0.0, 'Where are the lead-time anomalies concentrated and what is causing them?'))
        if lt['late_share'] > 0.2:
            worst_region = lt['by_region'][0]
            seasons = sorted(lt['by_season'].items(), key=lambda kv: kv[1], reverse=True)
            late_rev = float(df.loc[~df['on_time'], 'revenue'].sum())
            detail = (f'{_pct(lt["late_share"])} of deliveries miss the {OTIF_SLA_DAYS}-day SLA. '
                      f'{worst_region["region"]} is slowest at {worst_region["mean"]:.2f}d')
            if seasons:
                detail += f'; {seasons[0][0]} is the slowest season at {seasons[0][1]:.2f}d.'
            out.append(self._pill(
                'sla', 'WARNING', 'SLA breach rate above 20%', detail, ('Late share', _pct(lt['late_share'])),
                f'Set a {OTIF_SLA_DAYS}-day SLA with penalty clauses for {worst_region["region"]} suppliers.', late_rev * 0.02,
                'Why is delivery lag spiking during the Monsoon season?'))

        # 3. Margin leaks: promotions that discount more than they lift volume.
        if 'promotion_flag' in df.columns and df['promotion_flag'].nunique() > 1:
            promo, base = df[df['promotion_flag'] == 1], df[df['promotion_flag'] == 0]
            if len(promo) and len(base):
                lift = promo['units_sold'].mean() / base['units_sold'].mean() - 1
                discount = 1 - promo['price_unit'].mean() / base['price_unit'].mean()
                rev_ratio = promo['revenue'].mean() / base['revenue'].mean() - 1
                if rev_ratio < 0:
                    leak = float(-rev_ratio * base['revenue'].mean() * len(promo))
                    out.append(self._pill(
                        'margin', 'WARNING', 'Promotions dilute revenue',
                        f'Promo rows sell {_pct(lift, True)} units at a {_pct(discount)} price cut, so revenue per order falls {_pct(rev_ratio, True)}.',
                        ('Leak', _money(leak)), 'Restrict promotions to SKUs with proven elasticity; cap discount depth.', leak,
                        'Which promotions are leaking margin and where should we cut discount depth?'))
                elif lift > 0.15:
                    gain = float(rev_ratio * base['revenue'].mean() * len(promo))
                    out.append(self._pill(
                        'promo_win', 'OPPORTUNITY', 'Promotions are accretive',
                        f'Promoted orders lift units {_pct(lift, True)} with revenue per order {_pct(rev_ratio, True)}.',
                        ('Uplift', _money(gain)), 'Extend promotion calendar to the strongest-responding categories.', gain,
                        'Which categories respond best to promotions?'))

        # 4. Seasonal mismatch: stock positioned against the wrong season.
        seasonal = df.groupby('season').agg(units=('units_sold', 'sum'), stock=('stock_available', 'sum'))
        if len(seasonal) > 1:
            seasonal['ratio'] = seasonal['stock'] / seasonal['units'].replace(0, np.nan)
            avg = float(seasonal['ratio'].mean())
            peak = seasonal['units'].idxmax()
            low = seasonal['ratio'].idxmax()
            peak_ratio = float(seasonal.loc[peak, 'ratio'])
            if peak_ratio < avg * 0.97:
                out.append(self._pill(
                    'season_mismatch', 'WARNING', f'{peak} is under-stocked for its demand',
                    f'{peak} is the peak demand season but carries {peak_ratio:.1f} units of stock per unit sold vs {avg:.1f} on average.',
                    ('Stock/sales', f'{peak_ratio:.2f}x'), f'Pre-build inventory 3–4 weeks before {peak}.', 0.0,
                    f'How much should we pre-build before {peak} and in which regions?'))
            elif low != peak and float(seasonal.loc[low, 'ratio']) > avg * 1.05:
                out.append(self._pill(
                    'season_excess', 'OPPORTUNITY', f'Excess stock carried through {low}',
                    f'{low} holds {float(seasonal.loc[low, "ratio"]):.2f} units of stock per unit sold vs {avg:.2f} average.',
                    ('Stock/sales', f'{float(seasonal.loc[low, "ratio"]):.2f}x'), f'Draw down {low} safety stock and redeploy to {peak}.', 0.0,
                    f'How much safety stock can we release during {low}?'))

        # 5. Channel efficiency gap.
        cells = p['channel_region']['cells']
        if len(cells) > 1:
            best = max(cells, key=lambda c: c['rev_per_unit'])
            worst = min(cells, key=lambda c: c['rev_per_unit'])
            if worst['rev_per_unit'] and best['rev_per_unit'] / worst['rev_per_unit'] > 1.03:
                upside = (best['rev_per_unit'] - worst['rev_per_unit']) * worst['units'] * 0.1
                out.append(self._pill(
                    'channel', 'OPPORTUNITY', f'{best["channel"]} in {best["region"]} earns most per unit',
                    f'${best["rev_per_unit"]:.2f}/unit vs ${worst["rev_per_unit"]:.2f} for {worst["channel"]} in {worst["region"]}.',
                    ('Spread', f'${best["rev_per_unit"] - worst["rev_per_unit"]:.2f}'),
                    f'Shift 10% of {worst["region"]} {worst["channel"]} volume toward higher-yield channels.', upside,
                    'Suggest optimal regional inventory distribution across regions and channels'))

        # 6. Revenue momentum.
        rev = next(k for k in p['kpis'] if k['key'] == 'revenue')
        if rev['delta'] is not None and abs(rev['delta']) >= 0.05:
            down = rev['delta'] < 0
            out.append(self._pill(
                'momentum', 'WARNING' if down else 'OPPORTUNITY',
                f'Revenue {"down" if down else "up"} {_pct(abs(rev["delta"]))} {rev["delta_label"]}',
                f'Latest window revenue {_money(rev.get("window_value", 0))}.',
                ('Δ revenue', _pct(rev['delta'], True)),
                'Decompose the change by channel and region.' if down else 'Secure supply for the categories driving growth.',
                abs(rev['delta']) * rev.get('window_value', 0),
                'What is driving the latest revenue change by channel and region?'))

        out.sort(key=lambda i: (SEVERITY_RANK[i['severity']], -i['impact_usd']))
        return out[:limit]

    @staticmethod
    def _pill(pid: str, severity: str, title: str, detail: str, metric: tuple, action: str, impact: float, query: str) -> Dict[str, Any]:
        return {'id': pid, 'severity': severity, 'title': title, 'detail': detail,
                'metric': {'label': metric[0], 'value': metric[1]}, 'action': action,
                'impact_usd': round(float(impact), 2), 'query': query}

    # ------------------------------------------------------------------ offline analyst

    def offline_answer(self, query: str, filters: Optional[Dict[str, Any]] = None,
                       chart_context: Optional[Dict[str, Any]] = None) -> str:
        p = self.snapshot(filters)
        if p.get('empty'):
            return '**No rows match the current filters.** Clear a filter and ask again.'
        q = query.lower()
        k = {item['key']: item for item in p['kpis']}
        lt = p['lead_time']

        if chart_context:
            return self._answer_chart(query, chart_context, p)
        if re.search(r'simulat|what if|what-if|scenario|increase[sd]? by|\d+\s*%', q):
            return self._answer_scenario(q, filters, p)
        if re.search(r'stock ?out|at risk|reorder|safety stock|shortage', q):
            return self._answer_stockout(p, k)
        if re.search(r'lead|deliver|lag|monsoon|delay|carrier|logistic', q):
            return self._answer_lead(p, lt, filters)
        if re.search(r'distribut|allocat|region|north|south|east|west|rebalanc', q):
            return self._answer_distribution(p)
        return self._answer_general(p, k, lt)

    def _citations(self, items: List[str]) -> str:
        return '\n'.join(f'- {i}' for i in items)

    def _answer_stockout(self, p: Dict[str, Any], k: Dict[str, Any]) -> str:
        deficits = p['deficits']
        risk = k['stockout_risk']
        rows = '\n'.join(
            f'| {d["segment"]} | {d["stock"]:.0f} | {d["velocity"]:.1f} | {d["cover_days"]:.1f}d | {d["need_days"]:.1f}d | '
            f'{d["gap_units"]:.0f} | {_money(d["revenue_at_risk"])} |' for d in deficits)
        within_14 = [d for d in deficits if d['cover_days'] < 14]
        total = sum(d['revenue_at_risk'] for d in deficits)
        lead = deficits[0] if deficits else None
        return f"""### Executive answer
{len(within_14)} of the 5 tightest segments run out inside 14 days at current velocity. Stockout risk index is **{risk['value']:.1f}/100** ({risk.get('detail', '')}).

| Segment | Stock | Units/day | Cover | Need | Gap units | Revenue at risk |
|---|---:|---:|---:|---:|---:|---:|
{rows}

### Root cause hypothesis
Velocity over the last 7 days outpaces stock positioning. Cover is measured against lead time ({p['lead_time']['mean']:.2f}d) plus a 7-day review cycle, so any segment under ~{(lead['need_days'] if lead else 10):.0f} days of cover will miss replenishment.

### Tactical actions
1. **Expedite** {lead['segment'] if lead else 'the top segment'}: order {lead['gap_units'] if lead else 0:.0f}+ units now to reach its reorder point of {lead['reorder_point'] if lead else 0:.0f}. Est. protected revenue {_money(lead['revenue_at_risk'] if lead else 0)}.
2. **Raise safety stock** on the listed segments to a 95% service level (z = 1.65). Est. protected revenue across the list {_money(total)}.
3. **Daily review** on Critical Low quadrant SKUs until cover exceeds lead time + 7 days.

### Metric citations
{self._citations([f"Stockout risk index {risk['value']:.1f}", f"Mean lead time {p['lead_time']['mean']:.2f}d (σ {p['lead_time']['std']:.2f})", f"Quadrants: {p['velocity_matrix'].get('counts', {})}"])}
"""

    def _answer_lead(self, p: Dict[str, Any], lt: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> str:
        seasons = sorted(lt['by_season'].items(), key=lambda kv: kv[1], reverse=True)
        regions = lt['by_region']
        monsoon = lt['by_season'].get('Monsoon')
        overall = lt['mean']
        season_line = ', '.join(f'{s} {v:.2f}d' for s, v in seasons)
        region_rows = '\n'.join(f'| {r["region"]} | {r["mean"]:.2f} | {r["std"]:.2f} | {r["count"]:,} |' for r in regions)
        if monsoon is not None:
            gap = (monsoon - overall) / overall if overall else 0
            headline = (f'Monsoon lead time averages **{monsoon:.2f} days**, {_pct(gap, True)} vs the {overall:.2f}-day overall mean. '
                        + ('That is a material spike.' if gap > 0.05 else 'The data does not show a material Monsoon spike; the lag is structural, not seasonal.'))
        else:
            headline = f'Average lead time is **{overall:.2f} days** (σ {lt["std"]:.2f}); no Monsoon rows are in the current filter.'
        late_rev = sum(c['revenue'] * (1 - c['on_time']) for c in p['channel_region']['cells'])
        return f"""### Executive answer
{headline} {_pct(lt['late_share'])} of deliveries miss the {lt['sla_days']}-day SLA and {lt['anomaly_count']:,} exceed the 2σ threshold of {lt['anomaly_threshold']:.1f} days.

| Region | Mean days | σ | Orders |
|---|---:|---:|---:|
{region_rows}

### Root cause hypothesis
Seasonal ranking: {season_line}. Variance (σ {lt['std']:.2f}) is wide relative to the mean, which points to inconsistent carrier execution rather than distance. {regions[0]['region'] if regions else 'The slowest region'} carries the slowest lanes.

### Tactical actions
1. **Supplier SLA**: contract a {lt['sla_days']}-day SLA with a 2% penalty per late day for {regions[0]['region'] if regions else 'the slowest region'}. Revenue currently shipped late: {_money(late_rev)}.
2. **Buffer the season**: add {max(lt['p95'] - overall, 0):.1f} days of safety stock ahead of {seasons[0][0] if seasons else 'the slowest season'} (p95 minus mean lead time).
3. **Dual-source** the top-volume lanes where σ exceeds 1.2 days.

### Metric citations
{self._citations([f"Mean {overall:.2f}d, σ {lt['std']:.2f}, p95 {lt['p95']:.1f}d", f"Late share {_pct(lt['late_share'])}", f"By channel: " + ', '.join(f"{c['channel']} {c['mean']:.2f}d" for c in lt['by_channel'])])}
"""

    def _answer_scenario(self, q: str, filters: Optional[Dict[str, Any]], p: Dict[str, Any]) -> str:
        pct_match = re.search(r'(-?\d+(?:\.\d+)?)\s*%', q)
        days_match = re.search(r'(\d+)\s*days?', q)
        params: Dict[str, Any] = {}
        if 'demand' in q and pct_match:
            params['demand_shift_pct'] = float(pct_match.group(1))
        elif 'price' in q and pct_match:
            params['price_change_pct'] = float(pct_match.group(1))
        elif pct_match:
            params['lead_time_spike_pct'] = float(pct_match.group(1))
        if days_match and ('delay' in q or 'late' in q):
            params['delay_days'] = float(days_match.group(1))
        if not params:
            params['lead_time_spike_pct'] = 25.0
        result = self.simulate(params, filters)
        return self.scenario_narrative(result)

    def simulate(self, params: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        df = self.data.filtered(filters)
        if df.empty:
            raise ValueError('No rows match the current filters.')
        segments = self.data.segment_table(df)
        return simulate(segments, params, self.data.elasticity_coefficient(df))

    @staticmethod
    def scenario_narrative(result: Dict[str, Any]) -> str:
        b, s, prm = result['baseline'], result['scenario'], result['params']
        levers = []
        if prm['delay_days']:
            levers.append(f'+{prm["delay_days"]:.0f} days supplier delay')
        if prm['lead_time_spike_pct']:
            levers.append(f'{prm["lead_time_spike_pct"]:+.0f}% lead time')
        if prm['demand_shift_pct']:
            levers.append(f'{prm["demand_shift_pct"]:+.0f}% demand')
        if prm['price_change_pct']:
            levers.append(f'{prm["price_change_pct"]:+.0f}% price (elasticity {prm["price_elasticity_factor"]:.2f})')
        if prm['safety_stock_multiplier'] != 1:
            levers.append(f'{prm["safety_stock_multiplier"]:.2f}x safety stock')
        lever_text = ', '.join(levers) or 'baseline conditions'
        rows = '\n'.join(f'| {r["region"]} | {_money(r["baseline_lost_revenue"])} | {_money(r["lost_revenue"])} | {_pct(r["fill_rate"])} |'
                         for r in result['regions'])
        top = result['at_risk'][0] if result['at_risk'] else None
        delta_lost = s['lost_revenue'] - b['lost_revenue']
        return f"""### Executive answer
Under {lever_text}, projected {result['horizon_days']}-day lost sales move from **{_money(b['lost_revenue'])}** to **{_money(s['lost_revenue'])}** ({'+' if delta_lost >= 0 else '−'}{_money(abs(delta_lost))}). Fill rate goes {_pct(b['fill_rate'])} → {_pct(s['fill_rate'])}; demand-weighted stockout probability {_pct(b['stockout_probability'])} → {_pct(s['stockout_probability'])}.

| Region | Baseline lost | Scenario lost | Fill rate |
|---|---:|---:|---:|
{rows}

### Root cause hypothesis
Longer or more volatile lead time inflates lead-time demand (μ = d·L) and its spread (σ = √(L·σd² + d²·σL²)) while stock stays fixed, so z-scores fall and expected shortfall per cycle rises non-linearly.

### Tactical actions
1. **Buffer**: lift safety stock on {top['segment'] if top else 'the most exposed segments'} first; it alone loses {_money(top['lost_revenue']) if top else '$0'} in this scenario.
2. **Shorten the lane**: every day of delay removed is worth the slope of the delay curve (see simulator chart).
3. **Holding trade-off**: scenario carrying cost {_money(s['holding_cost'])} vs {_money(b['holding_cost'])} baseline over the horizon.

### Metric citations
{chr(10).join('- ' + a for a in result['assumptions'])}
"""

    def _answer_distribution(self, p: Dict[str, Any]) -> str:
        hm = p['heatmap']
        regions = p['sales_by_region']
        total_rev = sum(r['revenue'] for r in regions) or 1
        idx = {(c['season'], c['region']): c['index'] for c in hm['cells']}
        rows = []
        for r in regions:
            peak_season = max(hm['seasons'], key=lambda s: idx.get((s, r['region']), 0)) if hm['seasons'] else 'n/a'
            rows.append(f'| {r["region"]} | {_pct(r["revenue"] / total_rev)} | {_pct(r["share"])} | {peak_season} '
                        f'({idx.get((peak_season, r["region"]), 0):.2f}) | {r["avg_lead"]:.2f}d |')
        exposed: Dict[str, int] = {}
        for pnt in p['velocity_matrix']['points']:
            if pnt['quadrant'] == 'Critical Low':
                exposed[pnt['region']] = exposed.get(pnt['region'], 0) + 1
        over: Dict[str, int] = {}
        for pnt in p['velocity_matrix']['points']:
            if pnt['quadrant'] == 'Overstocked':
                over[pnt['region']] = over.get(pnt['region'], 0) + 1
        short_region = max(exposed, key=exposed.get) if exposed else None
        long_region = max(over, key=over.get) if over else None
        return f"""### Executive answer
Allocate inventory in proportion to unit share, then tilt toward the region with the most Critical Low segments{f' (**{short_region}**, {exposed[short_region]})' if short_region else ''}{f' and away from **{long_region}** ({over[long_region]} Overstocked)' if long_region else ''}.

| Region | Revenue share | Unit share | Peak season (index) | Lead time |
|---|---:|---:|---|---:|
{chr(10).join(rows)}

### Root cause hypothesis
Stock is positioned uniformly while demand is not: seasonal indices diverge by region, and the Critical Low quadrant concentrates where velocity outran replenishment.

### Tactical actions
1. **Transfer** stock from Overstocked to Critical Low segments in the same category before placing new POs.
2. **Seasonal targets**: set region stock targets = unit share × seasonal index × (lead time + 7d) × daily velocity.
3. **Review** allocation monthly; re-weight when a region's index moves more than ±0.1.

### Metric citations
{self._citations([f"Quadrants: {p['velocity_matrix'].get('counts', {})}", 'Seasonality index = daily units ÷ region average across seasons'])}
"""

    def _answer_chart(self, query: str, chart: Dict[str, Any], p: Dict[str, Any]) -> str:
        data = chart.get('data') or []
        numeric_keys: List[str] = []
        if data and isinstance(data[0], dict):
            numeric_keys = [key for key, v in data[0].items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        label_key = next((key for key in (data[0].keys() if data and isinstance(data[0], dict) else []) if key not in numeric_keys), None)
        summary = []
        for key in numeric_keys[:3]:
            vals = [(row.get(label_key, i), row.get(key)) for i, row in enumerate(data) if isinstance(row.get(key), (int, float))]
            if not vals:
                continue
            hi = max(vals, key=lambda v: v[1])
            lo = min(vals, key=lambda v: v[1])
            mean = sum(v for _, v in vals) / len(vals)
            spread = (hi[1] - lo[1]) / mean if mean else 0
            summary.append(f'| {key} | {hi[0]} ({hi[1]:,.2f}) | {lo[0]} ({lo[1]:,.2f}) | {mean:,.2f} | {_pct(spread)} |')
        table = '\n'.join(summary) or '| n/a | | | | |'
        return f"""### Executive answer
On **{chart.get('title', 'this chart')}**, the spread between the highest and lowest points is the signal to act on. {len(data)} data points were inspected under filters {p['filters'] or 'none'}.

| Measure | Highest | Lowest | Mean | Spread |
|---|---|---|---:|---:|
{table}

### Root cause hypothesis
Spreads above ~15% usually trace to allocation (stock not where demand is) or service (lead time variance of σ {p['lead_time']['std']:.2f}d) rather than price, given the fitted elasticity of {p['elasticity'].get('coefficient') if p['elasticity'].get('coefficient') is not None else 'n/a'}.

### Tactical actions
1. Drill into the lowest point with a filter and compare its lead time and cover against the highest.
2. If the gap persists across seasons, rebalance inventory toward the high performer.
3. Re-run this inspection after the next data refresh to confirm the trend.

### Metric citations
- Question: “{query}”
- Live Groq analysis is off; this answer was computed locally from the chart data.
"""

    def _answer_general(self, p: Dict[str, Any], k: Dict[str, Any], lt: Dict[str, Any]) -> str:
        insights = self.proactive_insights(p['filters'], limit=3)
        bullets = '\n'.join(f'{i + 1}. **{ins["title"]}**: {ins["action"]}' for i, ins in enumerate(insights)) or '1. Keep monitoring.'
        return f"""### Executive answer
Revenue is {_money(k['revenue']['value'])} ({_pct(k['revenue']['delta'], True)} {k['revenue']['delta_label']}), OTIF {_pct(k['otif']['value'])}, turnover {k['turnover']['value']:.1f}x/yr and stockout risk {k['stockout_risk']['value']:.1f}/100.

### Root cause hypothesis
{insights[0]['detail'] if insights else 'No threshold breaches detected in the current slice.'}

### Tactical actions
{bullets}

### Metric citations
{self._citations([f"Lead time {lt['mean']:.2f}d σ {lt['std']:.2f}", f"Rows analysed {p['rows']:,}", f"Window {p['date_range']['start']} → {p['date_range']['end']}"])}
"""
