import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from routes.analytics import router
from services.data_service import data_service
from utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title='Supply Chain Intelligence Dashboard API', version='1.0.0')

allowed_origins = os.getenv(
    'BACKEND_CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)

UPLOAD_DIR = Path(__file__).resolve().parent / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post('/upload')
async def upload_dataset(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open('wb') as buffer:
            buffer.write(await file.read())

        return data_service.process_upload(file_path, file.filename)
    except Exception as exc:
        logger.exception('Upload failed')
        raise HTTPException(status_code=400, detail=str(exc)) from exc
