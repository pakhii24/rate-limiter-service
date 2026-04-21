from pydantic import BaseModel
from typing import Optional

class CheckRequest(BaseModel):
    user_id: Optional[str] = None
    ip: str
    endpoint: str

class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    retry_after: int  # seconds until reset, 0 if allowed
    algorithm: str