from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.llm.controller import router as config_router
from controllers.cv.controller import router as cv_router
from controllers.search.controller import router as search_router
from controllers.scraper.controller import router as scraper_router
from controllers.ia.controller import router as ia_router

app = FastAPI(title="Huntarr API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router, prefix="/api")
app.include_router(cv_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(scraper_router, prefix="/api")
app.include_router(ia_router, prefix="/api")
