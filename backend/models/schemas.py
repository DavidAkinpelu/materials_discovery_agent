from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    reasoning_trace: List[Dict[str, Any]]
    search_results: Dict[str, Any]
    session_id: str
    images: Optional[List[Dict[str, Any]]] = []

