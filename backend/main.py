from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.config import router as config_router

app = FastAPI(title="Huntarr API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router, prefix="/api")
