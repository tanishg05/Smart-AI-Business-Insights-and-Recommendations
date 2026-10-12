import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from models.schemas import AIQueryRequest, ScenarioRequest
from services.data_service import data_service
from services.groq_service import groq_service
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix='/api/ai', tags=['ai'])


def _require_dataset() -> None:
    if not data_service.has_data:
        raise HTTPException(status_code=400, detail='No dataset loaded. Upload a CSV first.')


def _filters(region: Optional[str], channel: Optional[str], category: Optional[str], season: Optional[str],
             date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    return {'region': region, 'channel': channel, 'category': category, 'season': season,
            'date_from': date_from, 'date_to': date_to}


@router.get('/status')
def ai_status():
    return groq_service.status()


@router.post('/query')
def ai_query(request: AIQueryRequest):
    _require_dataset()
    history = [turn.model_dump() for turn in request.conversation_history or []]
    chart = request.chart_context.model_dump() if request.chart_context else None

    if not request.stream:
        try:
            return groq_service.query(request.query, request.context_filters, history, chart)
        except Exception as exc:
            logger.exception('AI query failed')
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def event_stream():
        try:
            for event in groq_service.stream_query(request.query, request.context_filters, history, chart):
                yield f'data: {json.dumps(event)}\n\n'
        except Exception as exc:
            logger.exception('AI stream failed')
            yield f'data: {json.dumps({"type": "error", "message": str(exc)})}\n\n'

    return StreamingResponse(event_stream(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@router.get('/proactive-insights')
def proactive_insights(region: Optional[str] = Query(None), channel: Optional[str] = Query(None),
                       category: Optional[str] = Query(None), season: Optional[str] = Query(None),
                       date_from: Optional[str] = Query(None), date_to: Optional[str] = Query(None)):
    _require_dataset()
    try:
        return groq_service.proactive_insights(_filters(region, channel, category, season, date_from, date_to))
    except Exception as exc:
        logger.exception('Proactive insights failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post('/scenario-simulate')
@router.post('/scenario')
def scenario_simulate(request: ScenarioRequest):
    _require_dataset()
    params = request.model_dump(exclude={'context_filters', 'include_narrative'})
    try:
        return groq_service.scenario(params, request.context_filters, request.include_narrative)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Scenario simulation failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc
