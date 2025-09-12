# # from fastapi import APIRouter
# # from app.models import QueryRequest, QueryResponse
# # from app.embeddings import detect_intent
# # from app.sql_generator import handle_sql
# # from app.forecast_service import handle_forecast

# # router = APIRouter()

# # @router.post("/query", response_model= QueryResponse)
# # def query_handler(req: QueryRequest):
# #     intent = detect_intent(req.prompt)
# #     #intent = "historical"  
# #     if intent == "historical":
# #         result = handle_sql(req.prompt)
# #     else:
# #         result = handle_forecast(req.prompt)

# #     return result        


# from fastapi import APIRouter
# from app.models import QueryRequest, QueryResponse
# from app.embeddings import detect_intent
# from app.sql_generator import handle_sql
# from app.forecast_service import handle_forecast

# router = APIRouter()

# @router.post("/query", response_model=QueryResponse)
# def query_handler(req: QueryRequest):
#     intent = detect_intent(req.prompt)

#     if intent == "historical":
#         result = handle_sql(req.prompt)
#     else:
#         # First fetch historical SQL data
#         hist_result = handle_sql(req.prompt)
#         if hist_result["data"]:
#             # Pass to forecasting
#             result = handle_forecast(req.prompt, hist_result["data"], chart_type="line")
#         else:
#             result = handle_forecast(req.prompt, None)

#     return result


from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse
from app.sql_generator import handle_sql

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def query_handler(req: QueryRequest):
    result = handle_sql(req.prompt)
    return result
