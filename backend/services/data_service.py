from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


class DataService:
    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.last_file_name = 'No file uploaded'

    def process_upload(self, file_path: Path, original_name: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path)

        required_columns = {'date', 'units_sold', 'price_unit', 'delivery_days', 'delivered_qty', 'stock_available'}
        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')

        processed = self._preprocess(df)
        self.df = processed
        self.last_file_name = original_name

        return self.get_full_payload(message='Dataset processed successfully', file_name=original_name, rows=len(processed))

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce')
        df['price_unit'] = pd.to_numeric(df['price_unit'], errors='coerce')
        df['delivery_days'] = pd.to_numeric(df['delivery_days'], errors='coerce')
        df['delivered_qty'] = pd.to_numeric(df['delivered_qty'], errors='coerce')
        df['stock_available'] = pd.to_numeric(df['stock_available'], errors='coerce')

        df = df[(df['units_sold'] > 0) & (df['price_unit'] > 0)].copy()
        df = df[df['date'].notna()].copy()

        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['season'] = df['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Summer', 4: 'Summer', 5: 'Summer',
            6: 'Monsoon', 7: 'Monsoon', 8: 'Monsoon',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
        })

        df['demand_class'] = np.where(df['units_sold'] > df['units_sold'].mean(), 'High Demand', 'Low Demand')
        df['is_weekend'] = df['date'].dt.weekday >= 5
        df['quarter'] = df['date'].dt.quarter

        df['lag_1'] = df['units_sold'].shift(1)
        df['rolling_mean_7'] = df['units_sold'].rolling(7, min_periods=1).mean()
        df = df.dropna(subset=['date', 'units_sold', 'price_unit', 'delivery_days', 'delivered_qty', 'stock_available']).reset_index(drop=True)

        return df

    def get_full_payload(self, message: str = 'Success', file_name: Optional[str] = None, rows: Optional[int] = None) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        payload = {
            'message': message,
            'file_name': file_name or self.last_file_name,
            'rows': rows if rows is not None else len(df),
            'summary': self._summary_metrics(df),
            'sales_trend': self._sales_trend(df),
            'sales_by_channel': self._group_sales(df, 'channel'),
            'sales_by_region': self._group_sales(df, 'region'),
            'category_sales': self._group_sales(df, 'category'),
            'seasonal_sales': self._seasonal_sales(df),
            'season_region_heatmap': self._season_region_heatmap(df),
            'delivery_distribution': self._delivery_distribution(df),
            'stock_sales': self._stock_sales(df),
            'demand_classification': self._demand_classification(df),
            'insights': self._insights(df),
            'recommendations': self._recommendation_engine(df),
            'forecast': self._forecast_next_period(df),
            'last_file_name': self.last_file_name
        }
        return payload

    def get_dashboard_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        return self.get_full_payload(message='Dashboard data loaded')

    def get_sales_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        return {
            'sales_by_channel': self._group_sales(df, 'channel'),
            'sales_by_region': self._group_sales(df, 'region'),
            'category_sales': self._group_sales(df, 'category')
        }

    def get_seasonality_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        return {
            'seasonal_sales': self._seasonal_sales(df),
            'season_region_heatmap': self._season_region_heatmap(df)
        }

    def get_operations_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        return {
            'delivery_distribution': self._delivery_distribution(df),
            'stock_sales': self._stock_sales(df)
        }

    def get_insights_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        return {
            'demand_classification': self._demand_classification(df),
            'insights': self._insights(df)
        }

    def get_recommendations_payload(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError('No dataset loaded. Upload a CSV first.')

        df = self.df
        return {
            'recommendations': self._recommendation_engine(df),
            'insights': self._insights(df)
        }

    def _summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        def safe_mean(series: pd.Series) -> float:
            value = series.mean()
            return float(value) if pd.notna(value) and np.isfinite(value) else 0.0

        total_sales = float(df['units_sold'].sum())
        avg_price = safe_mean(df['price_unit'])
        avg_delivery = safe_mean(df['delivery_days'])
        utilization = float(df['delivered_qty'].sum() / df['stock_available'].sum()) if df['stock_available'].sum() else 0.0

        return {
            'total_sales': total_sales,
            'avg_price': avg_price,
            'avg_delivery': avg_delivery,
            'utilization': utilization
        }

    def _sales_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        trend = df.groupby('date', as_index=False)['units_sold'].sum().sort_values('date')
        trend['date'] = trend['date'].dt.strftime('%Y-%m-%d')
        return trend.to_dict(orient='records')

    def _group_sales(self, df: pd.DataFrame, column: str) -> List[Dict[str, Any]]:
        grouped = df.groupby(column, as_index=False)['units_sold'].sum().sort_values('units_sold', ascending=False)
        return grouped.to_dict(orient='records')

    def _seasonal_sales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return df.groupby('season', as_index=False)['units_sold'].sum().to_dict(orient='records')

    def _season_region_heatmap(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return df.groupby(['season', 'region'], as_index=False)['units_sold'].sum().to_dict(orient='records')

    def _delivery_distribution(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return df.groupby('delivery_days', as_index=False).size().rename(columns={'size': 'count'}).to_dict(orient='records')

    def _stock_sales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return df[['stock_available', 'units_sold']].copy().reset_index(drop=True).to_dict(orient='records')

    def _demand_classification(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        counts = df['demand_class'].value_counts().reset_index()
        counts.columns = ['demand_class', 'count']
        return counts.to_dict(orient='records')

    def _insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {
                'high_demand_ratio': 0.0,
                'high_demand_season': 'N/A',
                'slow_region': 'N/A'
            }

        high_demand_ratio = float((df['demand_class'] == 'High Demand').mean())
        seasonal_sales = df.groupby('season')['units_sold'].sum()
        regional_sales = df.groupby('region')['units_sold'].sum()

        high_demand_season = seasonal_sales.idxmax() if not seasonal_sales.empty else 'N/A'
        slow_region = regional_sales.idxmin() if not regional_sales.empty else 'N/A'

        return {
            'high_demand_ratio': high_demand_ratio,
            'high_demand_season': high_demand_season,
            'slow_region': slow_region
        }

    def _recommendation_engine(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        recommendations = []
        utilization = float(df['delivered_qty'].sum() / df['stock_available'].sum()) if df['stock_available'].sum() else 0.0
        avg_delivery = float(df['delivery_days'].mean())

        if utilization < 0.75:
            recommendations.append({
                'title': 'Inventory Risk Detected',
                'description': 'Increase replenishment frequency and maintain higher safety stock.'
            })

        if avg_delivery > 5:
            recommendations.append({
                'title': 'Delivery Performance Risk',
                'description': 'Optimize logistics routes and review courier efficiency.'
            })

        if df['units_sold'].mean() > 0:
            recommendations.append({
                'title': 'Demand Monitoring',
                'description': 'Track SKU-level demand closely and improve forecasting accuracy.'
            })

        if not recommendations:
            recommendations.append({
                'title': 'Stable Operations',
                'description': 'Current operations are healthy. Keep monitoring seasonal patterns.'
            })

        return recommendations

    def _forecast_next_period(self, df: pd.DataFrame) -> Dict[str, Any]:
        values = df['units_sold'].tail(12).astype(float).to_numpy()
        if len(values) < 2:
            return {'forecast': float(values[-1]) if len(values) else 0.0, 'trend': 0.0}

        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        forecast = values[-1] + slope
        return {'forecast': float(forecast), 'trend': float(slope)}


data_service = DataService()
