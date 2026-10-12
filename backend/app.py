import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# backend/.env takes precedence over a root-level .env; real environment variables win over both.
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routes.ai import router as ai_router  # noqa: E402
from routes.analytics import router  # noqa: E402
from services.data_service import data_service  # noqa: E402
from utils.logging import get_logger  # noqa: E402

logger = get_logger(__name__)

app = FastAPI(title='Supply Chain Intelligence Dashboard API', version='2.0.0')

allowed_origins = [o.strip() for o in os.getenv(
    'BACKEND_CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)
app.include_router(ai_router)

UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event('startup')
def load_default_dataset() -> None:
    name = os.getenv('DEFAULT_DATASET', '').strip()
    if not name:
        return
    path = UPLOAD_DIR / Path(name).name
    if path.exists():
        try:
            data_service.process_upload(path, path.name)
        except Exception:
            logger.exception('Could not load DEFAULT_DATASET %s', path.name)


@app.post('/upload')
async def upload_dataset(file: UploadFile = File(...)):
    safe_name = Path(file.filename or 'upload.csv').name
    if not safe_name.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only .csv files are supported.')
    try:
        file_path = UPLOAD_DIR / safe_name
        with file_path.open('wb') as buffer:
            buffer.write(await file.read())

        return data_service.process_upload(file_path, safe_name)
    except Exception as exc:
        logger.exception('Upload failed')
        raise HTTPException(status_code=400, detail=str(exc)) from exc
