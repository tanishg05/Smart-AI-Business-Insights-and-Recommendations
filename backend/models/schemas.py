from typing import Any, Dict
from pydantic import BaseModel


class UploadResponse(BaseModel):
    message: str
    file_name: str
    rows: int
    summary: Dict[str, Any]
