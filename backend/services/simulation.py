"""What-if scenario engine.

Each SKU-location is modelled as a continuous-review inventory position:
lead-time demand ~ Normal(d·L, √(L·σd² + d²·σL²)). Stockout probability is the
chance that lead-time demand exceeds the stock on hand, and expected lost units
come from the standard normal loss function. Scenarios shift lead time, demand,
price and the safety-stock buffer, then the same model is re-evaluated.
"""
import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

HORIZON_DAYS = 30
HOLDING_RATE_ANNUAL = 0.25  # carrying cost as a share of inventory value per year

DEFAULT_PARAMS = {
    'delay_days': 0.0,                # supplier delivery delay added to lead time
    'lead_time_spike_pct': 0.0,       # proportional lead-time increase
    'demand_shift_pct': 0.0,          # seasonal / market demand change
    'safety_stock_multiplier': 1.0,   # buffer applied to stock on hand
    'price_change_pct': 0.0,          # list price change
    'price_elasticity_factor': None,  # None = use the dataset's fitted elasticity
}

_erf = np.vectorize(math.erf)


def _phi(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z ** 2) / math.sqrt(2 * math.pi)


def _cdf(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1 + _erf(z / math.sqrt(2)))


def normalize_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = {**DEFAULT_PARAMS, **{k: v for k, v in (params or {}).items() if k in DEFAULT_PARAMS and v is not None}}
    merged['delay_days'] = float(np.clip(float(merged['delay_days']), 0, 60))
    merged['lead_time_spike_pct'] = float(np.clip(float(merged['lead_time_spike_pct']), -50, 300))
    merged['demand_shift_pct'] = float(np.clip(float(merged['demand_shift_pct']), -90, 300))
    merged['safety_stock_multiplier'] = float(np.clip(float(merged['safety_stock_multiplier']), 0.1, 5))
    merged['price_change_pct'] = float(np.clip(float(merged['price_change_pct']), -80, 200))
    if merged['price_elasticity_factor'] is not None:
        merged['price_elasticity_factor'] = float(np.clip(float(merged['price_elasticity_factor']), -5, 0))
    return merged


def _evaluate(seg: pd.DataFrame, delay: float, spike: float, demand_mult: float,
              stock_mult: float, price_mult: float) -> pd.DataFrame:
    lead = (seg['lead_mean'].to_numpy() + delay) * (1 + spike / 100)
    lead = np.maximum(lead, 0.25)
    lead_std = seg['lead_std'].to_numpy() * (1 + spike / 100)
    demand = seg['velocity'].to_numpy() * demand_mult
    demand_std = seg['demand_std'].to_numpy() * demand_mult
    stock = seg['stock_now'].to_numpy() * stock_mult
    price = seg['price'].to_numpy() * price_mult

    mu = demand * lead
    sigma = np.sqrt(lead * demand_std ** 2 + demand ** 2 * lead_std ** 2)
    sigma = np.maximum(sigma, 1e-6)
    z = (stock - mu) / sigma
    p_stockout = 1 - _cdf(z)
    loss_per_cycle = sigma * (_phi(z) - z * (1 - _cdf(z)))
    cycles = HORIZON_DAYS / lead
    demand_horizon = demand * HORIZON_DAYS
    lost_units = np.minimum(loss_per_cycle * cycles, demand_horizon)

    out = seg[['segment', 'region', 'category']].copy()
    out['lead'] = lead
    out['demand'] = demand_horizon
    out['p_stockout'] = p_stockout
    out['lost_units'] = lost_units
    out['lost_revenue'] = lost_units * price
    out['revenue'] = (demand_horizon - lost_units) * price
    out['holding_cost'] = stock * price * HOLDING_RATE_ANNUAL * HORIZON_DAYS / 365
    out['stock'] = stock
    return out


def _totals(frame: pd.DataFrame) -> Dict[str, float]:
    demand = float(frame['demand'].sum())
    lost = float(frame['lost_units'].sum())
    weights = frame['demand'] / demand if demand else 1 / max(len(frame), 1)
    return {
        'demand_units': round(demand, 1),
        'lost_units': round(lost, 1),
        'lost_revenue': round(float(frame['lost_revenue'].sum()), 2),
        'projected_revenue': round(float(frame['revenue'].sum()), 2),
        'fill_rate': round(1 - lost / demand, 4) if demand else 1.0,
        'stockout_probability': round(float((frame['p_stockout'] * weights).sum()), 4),
        'segments_at_risk': int((frame['p_stockout'] > 0.2).sum()),
        'holding_cost': round(float(frame['holding_cost'].sum()), 2),
        'avg_lead_time': round(float(frame['lead'].mean()), 2),
    }


def simulate(segments: pd.DataFrame, params: Optional[Dict[str, Any]], fitted_elasticity: float) -> Dict[str, Any]:
    p = normalize_params(params)
    elasticity = p['price_elasticity_factor'] if p['price_elasticity_factor'] is not None else fitted_elasticity
    price_mult = 1 + p['price_change_pct'] / 100
    demand_mult = (1 + p['demand_shift_pct'] / 100) * (price_mult ** elasticity)

    baseline = _evaluate(segments, 0.0, 0.0, 1.0, 1.0, 1.0)
    scenario = _evaluate(segments, p['delay_days'], p['lead_time_spike_pct'], demand_mult,
                         p['safety_stock_multiplier'], price_mult)

    base_totals, scen_totals = _totals(baseline), _totals(scenario)
    deltas = {k: round(scen_totals[k] - base_totals[k], 4) for k in base_totals}

    regions: List[Dict[str, Any]] = []
    for region, part in scenario.groupby('region'):
        base_part = baseline[baseline['region'] == region]
        t, b = _totals(part), _totals(base_part)
        regions.append({'region': region, 'baseline_lost_revenue': b['lost_revenue'], 'lost_revenue': t['lost_revenue'],
                        'stockout_probability': t['stockout_probability'], 'fill_rate': t['fill_rate']})
    regions.sort(key=lambda r: r['lost_revenue'], reverse=True)

    at_risk = scenario.sort_values('lost_revenue', ascending=False).head(6)
    top = [{'segment': r['segment'], 'region': r['region'], 'category': r['category'],
            'p_stockout': round(float(r['p_stockout']), 4), 'lost_units': round(float(r['lost_units']), 1),
            'lost_revenue': round(float(r['lost_revenue']), 2)} for _, r in at_risk.iterrows()]

    # Sensitivity curve: lost revenue as delivery delay grows, holding the other levers fixed.
    curve = []
    for d in range(0, 16):
        frame = _evaluate(segments, float(d), p['lead_time_spike_pct'], demand_mult, p['safety_stock_multiplier'], price_mult)
        tot = _totals(frame)
        curve.append({'delay_days': d, 'lost_revenue': tot['lost_revenue'], 'stockout_probability': tot['stockout_probability']})

    return {
        'params': {**p, 'price_elasticity_factor': round(elasticity, 3)},
        'horizon_days': HORIZON_DAYS,
        'baseline': base_totals,
        'scenario': scen_totals,
        'deltas': deltas,
        'regions': regions,
        'at_risk': top,
        'delay_curve': curve,
        'assumptions': [
            f'{HORIZON_DAYS}-day horizon, continuous review, normal lead-time demand.',
            f'Demand multiplier {demand_mult:.3f} (shift × price^elasticity, elasticity {elasticity:.2f}).',
            f'Holding cost {HOLDING_RATE_ANNUAL:.0%} of inventory value per year.',
        ],
    }
