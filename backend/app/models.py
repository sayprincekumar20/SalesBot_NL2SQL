# from pydantic import BaseModel
# class QueryRequest(BaseModel):
#     prompt: str

# class QueryResponse(BaseModel):
#     intent:str
#     query: str | None = None
#     data: list | None = None
#     message: str | None = None    

from pydantic import BaseModel
from typing import Any, List, Optional, Dict

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    intent: str
    query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    chart: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    forecast: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
