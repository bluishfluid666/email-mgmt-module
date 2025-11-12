from typing import Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    detail: Optional[str] = None
    status_code: int

