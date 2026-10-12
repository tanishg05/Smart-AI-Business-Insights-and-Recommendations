import math
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = {'date', 'units_sold', 'price_unit', 'delivery_days', 'delivered_qty', 'stock_available'}
FILTER_DIMENSIONS = ('region', 'channel', 'category', 'season')
SEASON_ORDER = ['Winter', 'Summer', 'Monsoon', 'Autumn']
MONTH_TO_SEASON = {
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Summer', 4: 'Summer', 5: 'Summer',
    6: 'Monsoon', 7: 'Monsoon', 8: 'Monsoon',
    9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
}

# Operating assumptions used across KPIs, insights and the simulator.
OTIF_SLA_DAYS = 3          # an order is "on time" when delivered within this many days
REVIEW_PERIOD_DAYS = 7     # replenishment review cycle added to lead time for cover checks
SERVICE_Z = 1.65           # ~95% cycle service level for reorder points
VELOCITY_WINDOW_DAYS = 7   # rolling window for demand velocity


def _num(value: Any, digits: int = 4) -> float:
    """Convert numpy/pandas scalars to JSON-safe floats."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(f):
        return 0.0
    return round(f, digits)


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous == 0 or not math.isfinite(previous):
        return None
    return _num((current - previous) / abs(previous), 4)


class DataService:
    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.last_file_name = 'No file uploaded'
        self.loaded_at: Optional[str] = None
        self.has_sku = False
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ loading

    @property
    def has_data(self) -> bool:
        return self.df is not None and not self.df.empty

    def process_upload(self, file_path: Path, original_name: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')

        processed = self._preprocess(df)
        if processed.empty:
            raise ValueError('No valid rows after cleaning. Check dates, prices and quantities.')

        with self._lock:
            self.df = processed
            self.last_file_name = original_name
            self.loaded_at = datetime.now(timezone.utc).isoformat()
            self.has_sku = 'sku' in processed.columns
            self._cache.clear()

        logger.info('Loaded %s (%d rows)', original_name, len(processed))
        return self.get_full_payload(message='Dataset processed successfully', file_name=original_name, rows=len(processed))

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        for column in ['units_sold', 'price_unit', 'delivery_days', 'delivered_qty', 'stock_available']:
            df[column] = pd.to_numeric(df[column], errors='coerce')

        df = df.dropna(subset=['date', 'units_sold', 'price_unit', 'delivery_days', 'delivered_qty', 'stock_available'])
        df = df[(df['units_sold'] >= 0) & (df['price_unit'] > 0) & (df['stock_available'] >= 0)].copy()

        for column in ('region', 'channel', 'category'):
            if column not in df.columns:
                df[column] = 'All'
            df[column] = df[column].fillna('Unspecified').astype(str).str.strip()

        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['quarter'] = df['date'].dt.quarter
        if 'season' not in df.columns or df['season'].isna().all():
            df['season'] = df['month'].map(MONTH_TO_SEASON)
        df['season'] = df['season'].fillna(df['month'].map(MONTH_TO_SEASON)).astype(str)

        if 'demand_class' not in df.columns or df['demand_class'].isna().all():
            df['demand_class'] = np.where(df['units_sold'] > df['units_sold'].mean(), 'High Demand', 'Low Demand')

        if 'sku' in df.columns:
            df['sku'] = df['sku'].fillna('Unknown').astype(str)
            df['segment'] = df['sku'] + ' · ' + df['region']
        else:
            df['segment'] = df['category'] + ' · ' + df['region']

        df['revenue'] = df['units_sold'] * df['price_unit']
        df['is_weekend'] = df['date'].dt.weekday >= 5
        df['on_time'] = df['delivery_days'] <= OTIF_SLA_DAYS
        df['in_full'] = df['delivered_qty'] >= df['units_sold']

        df = df.sort_values('date').reset_index(drop=True)
        df['rolling_mean_7'] = df['units_sold'].rolling(7, min_periods=1).mean()
        return df

    # ------------------------------------------------------------------ filters

    def require_data(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')
        return self.df

    @staticmethod
    def normalize_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        clean: Dict[str, Any] = {}
        for key, value in (filters or {}).items():
            if value in (None, '', 'all', 'All', []):
                continue
            if key in FILTER_DIMENSIONS:
                values = value if isinstance(value, list) else str(value).split(',')
                values = [str(v).strip() for v in values if str(v).strip()]
                if values:
                    clean[key] = sorted(values)
            elif key in ('date_from', 'date_to'):
                clean[key] = str(value)
        return clean

    def filtered(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        df = self.require_data()
        filters = self.normalize_filters(filters)
        mask = pd.Series(True, index=df.index)
        for key in FILTER_DIMENSIONS:
            if key in filters:
                mask &= df[key].isin(filters[key])
        if 'date_from' in filters:
            mask &= df['date'] >= pd.to_datetime(filters['date_from'], errors='coerce')
        if 'date_to' in filters:
            mask &= df['date'] <= pd.to_datetime(filters['date_to'], errors='coerce')
        return df[mask]

    def filter_options(self) -> Dict[str, Any]:
        df = self.require_data()
        options: Dict[str, Any] = {}
        for key in FILTER_DIMENSIONS:
            values = df[key].dropna().unique().tolist()
            if key == 'season':
                values = [s for s in SEASON_ORDER if s in values] + sorted(v for v in values if v not in SEASON_ORDER)
            else:
                values = sorted(values)
            options[key] = values
        options['date_min'] = df['date'].min().strftime('%Y-%m-%d')
        options['date_max'] = df['date'].max().strftime('%Y-%m-%d')
        return options

    # ------------------------------------------------------------------ payloads

    def get_full_payload(self, message: str = 'Success', file_name: Optional[str] = None,
                         rows: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.require_data()
        filters = self.normalize_filters(filters)
        cache_key = repr(sorted(filters.items()))
        cached = self._cache.get(cache_key)
        if cached is None:
            cached = self._build_payload(self.filtered(filters))
            if len(self._cache) > 32:
                self._cache.clear()
            self._cache[cache_key] = cached

        return {
            **cached,
            'message': message,
            'file_name': file_name or self.last_file_name,
            'last_file_name': self.last_file_name,
            'total_rows': rows if rows is not None else len(self.df),
            'loaded_at': self.loaded_at,
            'filters': filters,
            'filter_options': self.filter_options(),
        }

    def _build_payload(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {'rows': 0, 'empty': True}

        segments = self.segment_table(df)
        lead_time = self._lead_time(df)
        trend = self._trend(df)
        return {
            'rows': int(len(df)),
            'empty': False,
            'granularity': trend['granularity'],
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d'),
                'days': int((df['date'].max() - df['date'].min()).days) + 1,
            },
            'summary': self._summary_metrics(df),
            'kpis': self._kpis(df, segments),
            'trend': trend['series'],
            'forecast_series': self._forecast_series(trend['series']),
            'sales_trend': self._sales_trend(df),
            'sales_by_channel': self._group_sales(df, 'channel'),
            'sales_by_region': self._group_sales(df, 'region'),
            'category_sales': self._group_sales(df, 'category'),
            'channel_region': self._channel_region(df),
            'elasticity': self._elasticity(df),
            'seasonal_sales': self._seasonal_sales(df),
            'season_region_heatmap': self._season_region_heatmap(df),
            'heatmap': self._heatmap(df),
            'lead_time': lead_time,
            'delivery_distribution': self._delivery_distribution(df),
            'velocity_matrix': self._velocity_matrix(segments),
            'deficits': self._deficits(segments),
            'stock_sales': self._stock_sales(df),
            'demand_classification': self._demand_classification(df),
            'insights': self._insights(df),
            'recommendations': self._recommendation_engine(df, segments, lead_time),
            'forecast': self._forecast_next_period(df),
        }

    def get_dashboard_payload(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.get_full_payload(message='Dashboard data loaded', filters=filters)

    def get_sales_payload(self) -> Dict[str, Any]:
        df = self.require_data()
        return {
            'sales_by_channel': self._group_sales(df, 'channel'),
            'sales_by_region': self._group_sales(df, 'region'),
            'category_sales': self._group_sales(df, 'category'),
            'channel_region': self._channel_region(df),
            'elasticity': self._elasticity(df),
        }

    def get_seasonality_payload(self) -> Dict[str, Any]:
        df = self.require_data()
        return {
            'seasonal_sales': self._seasonal_sales(df),
            'season_region_heatmap': self._season_region_heatmap(df),
            'heatmap': self._heatmap(df),
        }

    def get_operations_payload(self) -> Dict[str, Any]:
        df = self.require_data()
        segments = self.segment_table(df)
        return {
            'delivery_distribution': self._delivery_distribution(df),
            'lead_time': self._lead_time(df),
            'velocity_matrix': self._velocity_matrix(segments),
            'stock_sales': self._stock_sales(df),
        }

    def get_insights_payload(self) -> Dict[str, Any]:
        df = self.require_data()
        return {
            'demand_classification': self._demand_classification(df),
            'insights': self._insights(df),
        }

    def get_recommendations_payload(self) -> Dict[str, Any]:
        df = self.require_data()
        segments = self.segment_table(df)
        return {
            'recommendations': self._recommendation_engine(df, segments, self._lead_time(df)),
            'insights': self._insights(df),
        }

    # ------------------------------------------------------------------ building blocks

    @staticmethod
    def period_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """Return (current, previous, label): the latest window vs the window before it."""
        end = df['date'].max()
        span = (end - df['date'].min()).days + 1
        window = 28 if span >= 56 else max(1, span // 2)
        cur_start = end - pd.Timedelta(days=window - 1)
        prev_start = cur_start - pd.Timedelta(days=window)
        current = df[df['date'] >= cur_start]
        previous = df[(df['date'] >= prev_start) & (df['date'] < cur_start)]
        return current, previous, f'vs prior {window}d'

    @staticmethod
    def _resample_rule(df: pd.DataFrame) -> Tuple[str, str]:
        span = (df['date'].max() - df['date'].min()).days + 1
        return ('W-MON', 'week') if span > 120 else ('D', 'day')

    def segment_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Per SKU-location (or category-location) demand, stock and lead-time profile."""
        daily = (
            df.groupby(['segment', 'date'])
            .agg(units=('units_sold', 'sum'), stock=('stock_available', 'sum'))
            .reset_index()
        )
        last_date = df['date'].max()
        window_start = last_date - pd.Timedelta(days=VELOCITY_WINDOW_DAYS - 1)
        recent = daily[daily['date'] >= window_start]

        base = daily.groupby('segment').agg(
            demand_mean=('units', 'mean'),
            demand_std=('units', 'std'),
            stock_mean=('stock', 'mean'),
            units=('units', 'sum'),
            days=('date', 'nunique'),
        )
        lead = df.groupby('segment')['delivery_days'].agg(['mean', 'std']).rename(columns={'mean': 'lead_mean', 'std': 'lead_std'})
        meta = df.groupby('segment').agg(region=('region', 'first'), category=('category', 'first'),
                                         channel=('channel', 'first'), price=('price_unit', 'mean'),
                                         revenue=('revenue', 'sum'))
        recent_agg = recent.groupby('segment').agg(recent_units=('units', 'sum'), recent_days=('date', 'nunique'),
                                                   recent_stock=('stock', 'mean'))

        table = base.join(lead).join(meta).join(recent_agg)
        table['demand_std'] = table['demand_std'].fillna(table['demand_mean'] * 0.25)
        table['lead_std'] = table['lead_std'].fillna(0.0)
        # Velocity = average daily demand over the trailing window (per active day, so sparse data isn't penalised).
        table['velocity'] = table['recent_units'] / table['recent_days']
        table['velocity'] = table['velocity'].fillna(table['demand_mean'])
        table['stock_now'] = table['recent_stock'].fillna(table['stock_mean'])
        table['cover_days'] = np.where(table['velocity'] > 0, table['stock_now'] / table['velocity'], np.inf)
        table['reorder_point'] = (
            table['velocity'] * table['lead_mean']
            + SERVICE_Z * np.sqrt(table['lead_mean'] * table['demand_std'] ** 2 + table['velocity'] ** 2 * table['lead_std'] ** 2)
        )
        table['need_days'] = table['lead_mean'] + REVIEW_PERIOD_DAYS
        table['at_risk'] = table['stock_now'] < table['reorder_point']
        return table.reset_index()

    def _summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        stock_total = df['stock_available'].sum()
        return {
            'total_sales': _num(df['units_sold'].sum(), 2),
            'total_revenue': _num(df['revenue'].sum(), 2),
            'avg_price': _num(df['price_unit'].mean()),
            'avg_delivery': _num(df['delivery_days'].mean()),
            'delivery_std': _num(df['delivery_days'].std() if len(df) > 1 else 0.0),
            'utilization': _num(df['delivered_qty'].sum() / stock_total) if stock_total else 0.0,
            'otif': _num((df['on_time'] & df['in_full']).mean()),
            'sku_count': int(df['sku'].nunique()) if 'sku' in df.columns else None,
        }

    @staticmethod
    def risk_index(segments: pd.DataFrame) -> float:
        """0–100: demand-weighted share of segments whose stock covers less than lead time + review period."""
        if segments.empty:
            return 0.0
        exposure = (1 - segments['cover_days'] / segments['need_days']).clip(lower=0, upper=1)
        weights = segments['velocity'].clip(lower=0)
        if weights.sum() <= 0:
            return float(exposure.mean() * 100)
        return float((exposure * weights).sum() / weights.sum() * 100)

    def _kpis(self, df: pd.DataFrame, segments: pd.DataFrame) -> List[Dict[str, Any]]:
        current, previous, delta_label = self.period_split(df)
        rule, _ = self._resample_rule(df)
        frame = df.assign(otif=df['on_time'] & df['in_full']).set_index('date')
        series = frame.resample(rule).agg({
            'revenue': 'sum', 'units_sold': 'sum', 'stock_available': 'sum', 'delivery_days': 'mean', 'otif': 'mean'
        }).dropna(subset=['delivery_days']).tail(24)

        def turnover(part: pd.DataFrame) -> float:
            stock = part['stock_available'].sum()
            return float(part['units_sold'].sum() / stock * 365) if stock else 0.0

        def otif(part: pd.DataFrame) -> float:
            return float((part['on_time'] & part['in_full']).mean()) if len(part) else 0.0

        def mean_lead(part: pd.DataFrame) -> float:
            return float(part['delivery_days'].mean()) if len(part) else 0.0

        def status_for(value: float, good: float, warn: float, higher_is_better: bool = True) -> str:
            if higher_is_better:
                return 'healthy' if value >= good else 'warning' if value >= warn else 'critical'
            return 'healthy' if value <= good else 'warning' if value <= warn else 'critical'

        revenue_delta = _pct_change(float(current['revenue'].sum()), float(previous['revenue'].sum()))
        risk_now = self.risk_index(segments)
        risk_prev = self.risk_index(self.segment_table(previous)) if len(previous) else 0.0
        turn_series = (series['units_sold'] / series['stock_available'].replace(0, np.nan) * 365).fillna(0)
        lead_std = float(df['delivery_days'].std()) if len(df) > 1 else 0.0

        return [
            {
                'key': 'revenue', 'label': 'Total Revenue', 'format': 'currency',
                'value': _num(df['revenue'].sum(), 2), 'window_value': _num(current['revenue'].sum(), 2),
                'delta': revenue_delta, 'delta_label': delta_label, 'higher_is_better': True,
                'status': 'healthy' if (revenue_delta or 0) >= 0 else 'warning' if (revenue_delta or 0) > -0.1 else 'critical',
                'sparkline': [_num(v, 2) for v in series['revenue'].tolist()],
                'hint': 'Units sold × unit price across the filtered range.',
            },
            {
                'key': 'turnover', 'label': 'Inventory Turnover', 'format': 'turns',
                'value': _num(turnover(df), 2), 'delta': _pct_change(turnover(current), turnover(previous)),
                'delta_label': delta_label, 'higher_is_better': True, 'status': status_for(turnover(df), 12, 6),
                'sparkline': [_num(v, 2) for v in turn_series.tolist()],
                'hint': 'Annualised turns: units sold ÷ stock on hand × 365.',
            },
            {
                'key': 'otif', 'label': 'OTIF Rate', 'format': 'percent',
                'value': _num(otif(df)), 'delta': _pct_change(otif(current), otif(previous)), 'delta_label': delta_label,
                'higher_is_better': True, 'status': status_for(otif(df), 0.9, 0.75),
                'sparkline': [_num(v) for v in series['otif'].tolist()],
                'hint': f'Delivered within {OTIF_SLA_DAYS} days and in full (delivered ≥ sold).',
            },
            {
                'key': 'stockout_risk', 'label': 'Stockout Risk Index', 'format': 'index',
                'value': _num(risk_now, 1), 'delta': _pct_change(risk_now, risk_prev), 'delta_label': delta_label,
                'higher_is_better': False, 'status': status_for(risk_now, 15, 35, higher_is_better=False),
                'sparkline': [],
                'hint': f'0–100. Demand-weighted cover shortfall vs lead time + {REVIEW_PERIOD_DAYS}-day review.',
                'detail': f'{int(segments["at_risk"].sum())} of {len(segments)} below reorder point',
            },
            {
                'key': 'lead_time', 'label': 'Avg Lead Time', 'format': 'days',
                'value': _num(df['delivery_days'].mean(), 2), 'delta': _pct_change(mean_lead(current), mean_lead(previous)),
                'delta_label': delta_label, 'higher_is_better': False,
                'status': status_for(float(df['delivery_days'].mean()), OTIF_SLA_DAYS, OTIF_SLA_DAYS + 2, higher_is_better=False),
                'sparkline': [_num(v, 2) for v in series['delivery_days'].tolist()],
                'hint': f'Mean delivery days, σ {lead_std:.2f}.',
            },
        ]

    def _trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        rule, granularity = self._resample_rule(df)
        series = df.set_index('date').resample(rule).agg({'units_sold': 'sum', 'revenue': 'sum'})
        series = series[(series['units_sold'] > 0) | (series['revenue'] > 0)].copy()
        series['ma'] = series['units_sold'].rolling(7, min_periods=1).mean()
        series['revenue_ma'] = series['revenue'].rolling(7, min_periods=1).mean()
        out = [
            {
                'period': idx.strftime('%Y-%m-%d'),
                'units': _num(row['units_sold'], 2),
                'revenue': _num(row['revenue'], 2),
                'ma': _num(row['ma'], 2),
                'revenue_ma': _num(row['revenue_ma'], 2),
            }
            for idx, row in series.iterrows()
        ]
        return {'series': out, 'granularity': granularity}

    @staticmethod
    def _forecast_series(series: List[Dict[str, Any]], horizon: int = 7) -> Dict[str, Any]:
        """Holt's linear smoothing with a widening 95% band."""
        values = np.array([p['units'] for p in series], dtype=float)
        history = series[-36:]
        if len(values) < 3:
            return {'history': history, 'forecast': [], 'method': 'insufficient data'}

        # The final weekly bucket is often partial; leave it out of the fit so it doesn't drag the trend.
        fit_values = values[:-1] if len(values) > 8 else values
        alpha, beta = 0.45, 0.15
        level, trend = fit_values[0], fit_values[1] - fit_values[0]
        fitted = []
        for v in fit_values:
            fitted.append(level + trend)
            new_level = alpha * v + (1 - alpha) * (level + trend)
            trend = beta * (new_level - level) + (1 - beta) * trend
            level = new_level
        residuals = fit_values[1:] - np.array(fitted[1:])
        sigma = float(np.std(residuals)) if len(residuals) > 1 else float(fit_values.std())

        last = pd.to_datetime(series[-1]['period'])
        prev = pd.to_datetime(series[-2]['period'])
        step = last - prev if last > prev else pd.Timedelta(days=1)
        offset = 0 if len(fit_values) == len(values) else -1
        forecast = []
        for h in range(1, horizon + 1):
            steps = h - offset if offset else h
            point = max(0.0, level + steps * trend)
            band = 1.96 * sigma * math.sqrt(h)
            forecast.append({
                'period': (last + step * h).strftime('%Y-%m-%d'),
                'forecast': _num(point, 2),
                'lower': _num(max(0.0, point - band), 2),
                'upper': _num(point + band, 2),
            })
        denom = np.where(fit_values[1:] == 0, 1, fit_values[1:])
        mape = float(np.mean(np.abs(residuals / denom))) if len(residuals) else 0.0
        return {'history': history, 'forecast': forecast, 'method': "Holt's linear smoothing",
                'sigma': _num(sigma, 2), 'mape': _num(mape)}

    def _sales_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        trend = df.groupby('date', as_index=False)['units_sold'].sum().sort_values('date').tail(400)
        trend['date'] = trend['date'].dt.strftime('%Y-%m-%d')
        return trend.to_dict(orient='records')

    def _group_sales(self, df: pd.DataFrame, column: str) -> List[Dict[str, Any]]:
        grouped = df.groupby(column).agg(units_sold=('units_sold', 'sum'), revenue=('revenue', 'sum'),
                                         avg_price=('price_unit', 'mean'), avg_lead=('delivery_days', 'mean'))
        grouped = grouped.sort_values('units_sold', ascending=False).reset_index()
        total = grouped['units_sold'].sum() or 1
        return [
            {column: r[column], 'units_sold': _num(r['units_sold'], 2), 'revenue': _num(r['revenue'], 2),
             'avg_price': _num(r['avg_price']), 'avg_lead': _num(r['avg_lead']), 'share': _num(r['units_sold'] / total)}
            for _, r in grouped.iterrows()
        ]

    def _channel_region(self, df: pd.DataFrame) -> Dict[str, Any]:
        grouped = df.groupby(['region', 'channel']).agg(
            units=('units_sold', 'sum'), revenue=('revenue', 'sum'), on_time=('on_time', 'mean'),
            lead=('delivery_days', 'mean'), stock=('stock_available', 'sum'),
        ).reset_index()
        channels = sorted(grouped['channel'].unique().tolist())
        stacked = []
        for region, part in grouped.groupby('region'):
            row: Dict[str, Any] = {'region': region, 'total': _num(part['revenue'].sum(), 2)}
            for _, r in part.iterrows():
                row[r['channel']] = _num(r['revenue'], 2)
            stacked.append(row)
        stacked.sort(key=lambda r: r['total'], reverse=True)
        cells = [
            {'region': r['region'], 'channel': r['channel'], 'units': _num(r['units'], 2), 'revenue': _num(r['revenue'], 2),
             'on_time': _num(r['on_time']), 'lead': _num(r['lead']),
             'sell_through': _num(r['units'] / r['stock']) if r['stock'] else 0.0,
             'rev_per_unit': _num(r['revenue'] / r['units']) if r['units'] else 0.0}
            for _, r in grouped.iterrows()
        ]
        return {'channels': channels, 'stacked': stacked, 'cells': cells}

    def _elasticity(self, df: pd.DataFrame) -> Dict[str, Any]:
        frame = df[(df['units_sold'] > 0) & (df['price_unit'] > 0)]
        if len(frame) < 3 or frame['price_unit'].nunique() < 2:
            points = [{'price': _num(r['price_unit']), 'units': _num(r['units_sold']), 'category': r['category'], 'n': 1}
                      for _, r in frame.iterrows()]
            return {'points': points, 'trendline': [], 'coefficient': None, 'r2': None}

        if len(frame) <= 60:
            points = [{'price': _num(r['price_unit'], 3), 'units': _num(r['units_sold'], 2), 'category': r['category'], 'n': 1}
                      for _, r in frame.iterrows()]
        else:
            bins = min(12, frame['price_unit'].nunique())
            binned = frame.assign(price_bin=pd.qcut(frame['price_unit'], q=bins, duplicates='drop'))
            grouped = binned.groupby(['category', 'price_bin'], observed=True).agg(
                price=('price_unit', 'mean'), units=('units_sold', 'mean'), n=('units_sold', 'size')).reset_index()
            points = [{'price': _num(r['price'], 3), 'units': _num(r['units'], 2), 'category': r['category'], 'n': int(r['n'])}
                      for _, r in grouped.iterrows() if r['n'] > 0]

        x, y = np.log(frame['price_unit'].to_numpy()), np.log(frame['units_sold'].to_numpy())
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        ss_res, ss_tot = float(((y - pred) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
        grid = np.linspace(frame['price_unit'].min(), frame['price_unit'].max(), 24)
        trend = [{'price': _num(p, 3), 'units': _num(math.exp(intercept) * p ** slope, 2)} for p in grid]
        return {'points': points, 'trendline': trend, 'coefficient': _num(slope, 3), 'r2': _num(r2, 3)}

    def elasticity_coefficient(self, df: pd.DataFrame) -> float:
        coef = self._elasticity(df).get('coefficient')
        # Clamp to a plausible range; noisy datasets can produce positive or extreme slopes.
        if coef is None:
            return -1.0
        return float(min(-0.1, max(-3.0, coef)))

    def _seasonal_sales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        grouped = df.groupby('season').agg(units_sold=('units_sold', 'sum'), revenue=('revenue', 'sum')).reset_index()
        order = {s: i for i, s in enumerate(SEASON_ORDER)}
        grouped['o'] = grouped['season'].map(order).fillna(99)
        grouped = grouped.sort_values('o').drop(columns='o')
        return [{'season': r['season'], 'units_sold': _num(r['units_sold'], 2), 'revenue': _num(r['revenue'], 2)}
                for _, r in grouped.iterrows()]

    def _season_region_heatmap(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        grouped = df.groupby(['season', 'region'], as_index=False)['units_sold'].sum()
        return [{'season': r['season'], 'region': r['region'], 'units_sold': _num(r['units_sold'], 2)} for _, r in grouped.iterrows()]

    def _heatmap(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Normalise by active days so seasons with more data don't dominate.
        grouped = df.groupby(['season', 'region']).agg(units=('units_sold', 'sum'), days=('date', 'nunique'),
                                                       lead=('delivery_days', 'mean')).reset_index()
        grouped['daily'] = grouped['units'] / grouped['days'].replace(0, np.nan)
        region_avg = grouped.groupby('region')['daily'].transform('mean')
        grouped['index'] = grouped['daily'] / region_avg
        present = grouped['season'].unique().tolist()
        seasons = [s for s in SEASON_ORDER if s in present] + sorted(s for s in present if s not in SEASON_ORDER)
        cells = [{'season': r['season'], 'region': r['region'], 'units': _num(r['units'], 2),
                  'daily': _num(r['daily'], 2), 'index': _num(r['index'], 3), 'lead': _num(r['lead'], 2)}
                 for _, r in grouped.iterrows()]
        return {'seasons': seasons, 'regions': sorted(grouped['region'].unique().tolist()), 'cells': cells}

    def _lead_time(self, df: pd.DataFrame) -> Dict[str, Any]:
        lead = df['delivery_days']
        mean = float(lead.mean())
        std = float(lead.std()) if len(lead) > 1 else 0.0
        threshold = mean + 2 * std
        counts = lead.round().value_counts().sort_index()
        n = len(lead)
        histogram = []
        for days, count in counts.items():
            if std > 0:
                normal = n * math.exp(-0.5 * ((days - mean) / std) ** 2) / (std * math.sqrt(2 * math.pi))
            else:
                normal = float(count)
            histogram.append({'days': _num(days, 1), 'count': int(count), 'normal': _num(normal, 2),
                              'anomaly': bool(std > 0 and days > threshold)})
        by_region = (df.groupby('region')['delivery_days'].agg(['mean', 'std', 'count']).reset_index()
                     .sort_values('mean', ascending=False))
        by_channel = (df.groupby('channel')['delivery_days'].agg(['mean', 'std']).reset_index()
                      .sort_values('mean', ascending=False))
        by_season = df.groupby('season')['delivery_days'].mean()
        return {
            'histogram': histogram,
            'mean': _num(mean, 3), 'std': _num(std, 3),
            'p95': _num(lead.quantile(0.95), 2),
            'anomaly_threshold': _num(threshold, 2),
            'anomaly_count': int((lead > threshold).sum()) if std > 0 else 0,
            'sla_days': OTIF_SLA_DAYS,
            'late_share': _num((lead > OTIF_SLA_DAYS).mean()),
            'by_region': [{'region': r['region'], 'mean': _num(r['mean'], 3), 'std': _num(r['std'], 3), 'count': int(r['count'])}
                          for _, r in by_region.iterrows()],
            'by_channel': [{'channel': r['channel'], 'mean': _num(r['mean'], 3), 'std': _num(r['std'], 3)}
                           for _, r in by_channel.iterrows()],
            'by_season': {k: _num(v, 3) for k, v in by_season.items()},
        }

    def _delivery_distribution(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        dist = df.groupby('delivery_days').size().reset_index(name='count')
        return [{'delivery_days': _num(r['delivery_days'], 2), 'count': int(r['count'])} for _, r in dist.iterrows()]

    def _velocity_matrix(self, segments: pd.DataFrame) -> Dict[str, Any]:
        if segments.empty:
            return {'points': [], 'x_split': 0, 'y_split': 0, 'counts': {}}
        x_split = float(segments['velocity'].median())
        y_split = float(segments['stock_now'].median())

        def quadrant(row: pd.Series) -> str:
            fast = row['velocity'] >= x_split
            high = row['stock_now'] >= y_split
            if fast and not high:
                return 'Critical Low'
            if fast and high:
                return 'Fast Mover'
            if not fast and high:
                return 'Overstocked'
            return 'Dead Stock'

        seg = segments.copy()
        seg['quadrant'] = seg.apply(quadrant, axis=1)
        points = [
            {'segment': r['segment'], 'region': r['region'], 'category': r['category'],
             'velocity': _num(r['velocity'], 2), 'stock': _num(r['stock_now'], 1),
             'cover_days': _num(min(r['cover_days'], 999), 1), 'reorder_point': _num(r['reorder_point'], 1),
             'lead': _num(r['lead_mean'], 2), 'quadrant': r['quadrant'], 'at_risk': bool(r['at_risk'])}
            for _, r in seg.iterrows()
        ]
        return {'points': points, 'x_split': _num(x_split, 2), 'y_split': _num(y_split, 1),
                'counts': {k: int(v) for k, v in seg['quadrant'].value_counts().items()},
                'unit': 'SKU-location' if self.has_sku else 'category-location'}

    def _deficits(self, segments: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
        if segments.empty:
            return []
        seg = segments.copy()
        seg['gap'] = seg['reorder_point'] - seg['stock_now']
        seg['cover_ratio'] = seg['cover_days'] / seg['need_days']
        seg = seg.sort_values(['cover_ratio', 'gap'], ascending=[True, False]).head(limit)
        return [
            {'segment': r['segment'], 'region': r['region'], 'category': r['category'],
             'stock': _num(r['stock_now'], 1), 'velocity': _num(r['velocity'], 2),
             'cover_days': _num(min(r['cover_days'], 999), 1), 'need_days': _num(r['need_days'], 1),
             'reorder_point': _num(r['reorder_point'], 1), 'gap_units': _num(max(r['gap'], 0), 1),
             'revenue_at_risk': _num(max(r['need_days'] - r['cover_days'], 0) * r['velocity'] * r['price'], 2),
             'at_risk': bool(r['at_risk'])}
            for _, r in seg.iterrows()
        ]

    def _stock_sales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        sample = df[['stock_available', 'units_sold']]
        if len(sample) > 500:
            sample = sample.sample(500, random_state=7)
        return sample.reset_index(drop=True).to_dict(orient='records')

    def _demand_classification(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        counts = df['demand_class'].value_counts().reset_index()
        counts.columns = ['demand_class', 'count']
        return [{'demand_class': r['demand_class'], 'count': int(r['count'])} for _, r in counts.iterrows()]

    def _insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {'high_demand_ratio': 0.0, 'high_demand_season': 'N/A', 'slow_region': 'N/A'}
        seasonal_sales = df.groupby('season')['units_sold'].sum()
        regional_sales = df.groupby('region')['units_sold'].sum()
        return {
            'high_demand_ratio': _num((df['demand_class'] == 'High Demand').mean()),
            'high_demand_season': seasonal_sales.idxmax() if not seasonal_sales.empty else 'N/A',
            'slow_region': regional_sales.idxmin() if not regional_sales.empty else 'N/A',
        }

    def _recommendation_engine(self, df: pd.DataFrame, segments: pd.DataFrame, lead_time: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        at_risk = segments[segments['at_risk']] if len(segments) else segments
        if len(at_risk):
            gap = float((at_risk['reorder_point'] - at_risk['stock_now']).clip(lower=0).sum())
            recs.append({
                'title': 'Lift reorder points on exposed SKU-locations',
                'description': f'{len(at_risk)} of {len(segments)} segments sit below a 95% service reorder point. '
                               f'Raising stock by ~{gap:,.0f} units closes the gap.',
                'severity': 'critical' if len(at_risk) / max(len(segments), 1) > 0.25 else 'warning',
            })

        late_share = lead_time.get('late_share', 0)
        if late_share > 0.2 and lead_time.get('by_region'):
            worst = lead_time['by_region'][0]
            recs.append({
                'title': f'Tighten supplier SLA in {worst["region"]}',
                'description': f'{late_share:.0%} of deliveries exceed the {OTIF_SLA_DAYS}-day SLA. '
                               f'{worst["region"]} averages {worst["mean"]:.2f} days (σ {worst["std"]:.2f}).',
                'severity': 'warning',
            })

        if len(segments):
            over = segments[segments['cover_days'] > segments['need_days'] * 3]
            if len(over):
                excess_units = (over['stock_now'] - over['need_days'] * 2 * over['velocity']).clip(lower=0)
                tied = float((excess_units * over['price']).sum())
                recs.append({
                    'title': 'Release excess stock from slow movers',
                    'description': f'{len(over)} segments hold more than 3× their replenishment need; '
                                   f'about ${tied:,.0f} of inventory value could be redeployed.',
                    'severity': 'opportunity',
                })

        channel = df.groupby('channel')['revenue'].sum().sort_values()
        if len(channel) > 1:
            recs.append({
                'title': f'Rebalance mix toward {channel.index[-1]}',
                'description': f'{channel.index[-1]} drives ${channel.iloc[-1]:,.0f} vs ${channel.iloc[0]:,.0f} in {channel.index[0]}. '
                               'Shift promotional allocation to the stronger channel.',
                'severity': 'opportunity',
            })

        if not recs:
            recs.append({'title': 'Stable operations', 'description': 'No threshold breaches. Keep monitoring seasonal patterns.',
                         'severity': 'healthy'})
        return recs

    def _forecast_next_period(self, df: pd.DataFrame) -> Dict[str, Any]:
        values = df.groupby('date')['units_sold'].sum().tail(12).astype(float).to_numpy()
        if len(values) < 2:
            return {'forecast': float(values[-1]) if len(values) else 0.0, 'trend': 0.0}
        slope = np.polyfit(np.arange(len(values)), values, 1)[0]
        return {'forecast': _num(values[-1] + slope, 2), 'trend': _num(slope, 3)}


data_service = DataService()
