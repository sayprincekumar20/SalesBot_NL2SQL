# from fastapi import FastAPI
# from app.routes import router
# from dotenv import load_dotenv
# import os
# from pathlib import Path
# from fastapi.middleware.cors import CORSMiddleware
# from pathlib import Path




# # Explicitly load .env from project root
# BASE_DIR = Path(__file__).resolve().parent.parent
# dotenv_path = BASE_DIR / ".env"
# load_dotenv(dotenv_path)

# print("DEBUG OPENAI KEY:", os.getenv("OPENAI_API_KEY")) 


# app=FastAPI(tittle= "SQL + Forecast API", version="1.0")

# # add CORS Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins =["*"],
#     allow_credentials =True,
#     allow_methods= ["*"],
#     allow_headers= ["*"],
#  )
# app.include_router(router)

from fastapi import FastAPI
from app.routes import router
from dotenv import load_dotenv
import os
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)

app = FastAPI(title="SQL + Forecast API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
