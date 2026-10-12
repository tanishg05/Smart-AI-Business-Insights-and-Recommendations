from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.schemas import DatasetLoadRequest
from services.data_service import data_service

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / 'uploads'


def _filters(region, channel, category, season, date_from, date_to):
    return {'region': region, 'channel': channel, 'category': category, 'season': season,
            'date_from': date_from, 'date_to': date_to}


@router.get('/health')
def health():
    return {'status': 'ok', 'dataset_loaded': data_service.has_data}


@router.get('/dashboard')
def dashboard(region: Optional[str] = Query(None), channel: Optional[str] = Query(None),
              category: Optional[str] = Query(None), season: Optional[str] = Query(None),
              date_from: Optional[str] = Query(None), date_to: Optional[str] = Query(None)):
    try:
        return data_service.get_dashboard_payload(_filters(region, channel, category, season, date_from, date_to))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/sales')
def sales():
    try:
        return data_service.get_sales_payload()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/seasonality')
def seasonality():
    try:
        return data_service.get_seasonality_payload()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/operations')
def operations():
    try:
        return data_service.get_operations_payload()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/insights')
def insights():
    try:
        return data_service.get_insights_payload()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/recommendations')
def recommendations():
    try:
        return data_service.get_recommendations_payload()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/api/datasets')
def list_datasets():
    files = sorted(UPLOAD_DIR.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        'active': data_service.last_file_name if data_service.has_data else None,
        'datasets': [{'file_name': f.name, 'size_kb': round(f.stat().st_size / 1024, 1)} for f in files],
    }


@router.post('/api/datasets/load')
def load_dataset(request: DatasetLoadRequest):
    available = {f.name: f for f in UPLOAD_DIR.glob('*.csv')}
    target = available.get(Path(request.file_name).name)
    if target is None:
        raise HTTPException(status_code=404, detail=f'Dataset {request.file_name} not found in uploads.')
    try:
        return data_service.process_upload(target, target.name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
