"""Groq LLM integration with context hydration, streaming and an offline fallback.

The API key is read from the environment (GROQ_API_KEY, loaded from backend/.env)
and is never logged or returned to clients. When the key is missing or a Groq
call fails, responses fall back to the deterministic InsightEngine so the UI
keeps working.
"""
import json
import os
from typing import Any, Dict, Iterator, List, Optional

from services.data_service import data_service
from services.insight_engine import InsightEngine
from utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = 'llama-3.3-70b-versatile'
MAX_HISTORY_TURNS = 8

PERSONA = (
    'You are an elite Chief Supply Chain Officer and Quantitative Operations Analyst. '
    'You analyze data rigorously with exact numbers, avoid fluff, avoid generic advice, and provide concrete '
    'operational strategies (reorder thresholds, safety stock buffers, channel reallocations, supplier SLAs).'
)

ANSWER_FORMAT = """Answer in GitHub-flavoured markdown with exactly these sections:
### Executive answer
One or two sentences with the direct answer and the key number.
### Root cause hypothesis
The most likely driver, tied to specific metrics.
### Tactical actions
A numbered list. Each action names the lever, the target value, and an estimated financial impact in dollars.
### Metric citations
Bullets quoting the exact figures from the DATA BRIEF you relied on.
Use a markdown table when comparing 3+ items. Only use numbers present in the DATA BRIEF or derived from them; if data is missing, say so.
Glossary: velocity = avg daily units over the last 7 days; cover = stock ÷ velocity (days); need = lead time + 7-day review; reorder point uses a 95% service level."""


class GroqService:
    def __init__(self) -> None:
        self.engine = InsightEngine(data_service)
        self._client = None
        self._client_key: Optional[str] = None

    # ------------------------------------------------------------------ config

    @property
    def api_key(self) -> Optional[str]:
        key = os.getenv('GROQ_API_KEY', '').strip()
        return key or None

    @property
    def model(self) -> str:
        return os.getenv('GROQ_MODEL', DEFAULT_MODEL).strip() or DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return self.api_key is not None

    def status(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'model': self.model if self.enabled else None,
            'mode': 'groq' if self.enabled else 'engine',
            'dataset_loaded': data_service.has_data,
            'dataset': data_service.last_file_name if data_service.has_data else None,
        }

    def _get_client(self):
        key = self.api_key
        if key is None:
            return None
        if self._client is None or self._client_key != key:
            from groq import Groq  # imported lazily so the app runs without the package installed
            self._client = Groq(api_key=key, timeout=60.0, max_retries=1)
            self._client_key = key
        return self._client

    # ------------------------------------------------------------------ prompting

    def _messages(self, query: str, filters: Optional[Dict[str, Any]], history: Optional[List[Dict[str, str]]],
                  chart_context: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        brief = self.engine.build_context(filters, chart_context)
        system = f'{PERSONA}\n\n{ANSWER_FORMAT}\n\nDATA BRIEF\n{brief}'
        messages: List[Dict[str, str]] = [{'role': 'system', 'content': system}]
        for turn in (history or [])[-MAX_HISTORY_TURNS * 2:]:
            role = turn.get('role')
            content = str(turn.get('content', ''))[:4000]
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': query.strip()[:2000]})
        return messages

    # ------------------------------------------------------------------ query

    def stream_query(self, query: str, filters: Optional[Dict[str, Any]] = None,
                     history: Optional[List[Dict[str, str]]] = None,
                     chart_context: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """Yield events: meta → delta* → done (or error)."""
        client = self._get_client()
        if client is not None:
            try:
                messages = self._messages(query, filters, history, chart_context)
                stream = client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.2, max_tokens=1400, stream=True)
                yield {'type': 'meta', 'source': 'groq', 'model': self.model}
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield {'type': 'delta', 'text': delta}
                yield {'type': 'done'}
                return
            except Exception as exc:  # network, auth, rate limit…
                logger.warning('Groq query failed, using offline engine: %s', type(exc).__name__)
                note = f'> Groq was unreachable ({type(exc).__name__}); showing the local analytics engine instead.\n\n'
                yield {'type': 'meta', 'source': 'engine', 'model': None, 'fallback_reason': type(exc).__name__}
                yield from self._chunked(note + self.engine.offline_answer(query, filters, chart_context))
                yield {'type': 'done'}
                return

        yield {'type': 'meta', 'source': 'engine', 'model': None}
        yield from self._chunked(self.engine.offline_answer(query, filters, chart_context))
        yield {'type': 'done'}

    def query(self, query: str, filters: Optional[Dict[str, Any]] = None,
              history: Optional[List[Dict[str, str]]] = None,
              chart_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        source, model, parts = 'engine', None, []
        for event in self.stream_query(query, filters, history, chart_context):
            if event['type'] == 'meta':
                source, model = event['source'], event.get('model')
            elif event['type'] == 'delta':
                parts.append(event['text'])
        return {'answer': ''.join(parts), 'source': source, 'model': model}

    @staticmethod
    def _chunked(text: str, size: int = 18) -> Iterator[Dict[str, Any]]:
        # Emit word-ish chunks so the offline engine streams like a model would.
        words = text.split(' ')
        for i in range(0, len(words), size):
            piece = ' '.join(words[i:i + size])
            yield {'type': 'delta', 'text': piece + (' ' if i + size < len(words) else '')}

    # ------------------------------------------------------------------ proactive insights

    def proactive_insights(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pills = self.engine.proactive_insights(filters)
        client = self._get_client()
        if client is None or not pills:
            return {'insights': pills, 'source': 'engine', 'model': None}

        try:
            brief = self.engine.build_context(filters)
            prompt = (
                'Rewrite these detected supply chain signals as sharp executive insight pills. Keep the same ids, severities and '
                'numbers; tighten wording; make each action concrete (lever + target + owner). Return JSON '
                '{"insights":[{"id","title","detail","action"}]}. Titles under 60 characters, detail under 200, action under 140.\n\n'
                f'SIGNALS\n{json.dumps([{k: p[k] for k in ("id", "severity", "title", "detail", "action")} for p in pills])}'
            )
            response = client.chat.completions.create(
                model=self.model, temperature=0.2, max_tokens=1200,
                response_format={'type': 'json_object'},
                messages=[{'role': 'system', 'content': f'{PERSONA}\n\nDATA BRIEF\n{brief}'},
                          {'role': 'user', 'content': prompt}])
            rewritten = json.loads(response.choices[0].message.content or '{}').get('insights', [])
            by_id = {r.get('id'): r for r in rewritten if isinstance(r, dict)}
            for pill in pills:
                patch = by_id.get(pill['id'])
                if patch:
                    for field in ('title', 'detail', 'action'):
                        if isinstance(patch.get(field), str) and patch[field].strip():
                            pill[field] = patch[field].strip()
            return {'insights': pills, 'source': 'groq', 'model': self.model}
        except Exception as exc:
            logger.warning('Groq insight polish failed: %s', type(exc).__name__)
            return {'insights': pills, 'source': 'engine', 'model': None, 'fallback_reason': type(exc).__name__}

    # ------------------------------------------------------------------ scenarios

    def scenario(self, params: Dict[str, Any], filters: Optional[Dict[str, Any]] = None,
                 include_narrative: bool = True) -> Dict[str, Any]:
        result = self.engine.simulate(params, filters)
        if not include_narrative:
            return {**result, 'narrative': None, 'source': 'engine'}

        client = self._get_client()
        if client is not None:
            try:
                compact = {k: result[k] for k in ('params', 'horizon_days', 'baseline', 'scenario', 'deltas', 'regions', 'at_risk')}
                compact['delay_curve'] = result['delay_curve'][::3]
                messages = self._messages(
                    'Interpret this what-if simulation for the executive team. Quantify the financial exposure, name the regions and '
                    'segments to act on first, and give mitigation levers with target values.\n\nSIMULATION\n'
                    + json.dumps(compact, separators=(',', ':')),
                    filters, None, None)
                response = client.chat.completions.create(model=self.model, messages=messages, temperature=0.2, max_tokens=1200)
                return {**result, 'narrative': response.choices[0].message.content, 'source': 'groq', 'model': self.model}
            except Exception as exc:
                logger.warning('Groq scenario narrative failed: %s', type(exc).__name__)
        return {**result, 'narrative': self.engine.scenario_narrative(result), 'source': 'engine'}


groq_service = GroqService()
