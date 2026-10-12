from fastapi import APIRouter, HTTPException

from services.data_service import data_service

router = APIRouter()


@router.get('/health')
def health():
    return {'status': 'ok'}


@router.get('/dashboard')
def dashboard():
    try:
        return data_service.get_dashboard_payload()
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
