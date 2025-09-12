from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse
from app.sql_generator import handle_sql

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def query_handler(req: QueryRequest):
    result = handle_sql(req.prompt)
    return result
