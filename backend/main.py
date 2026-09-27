from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.commodities import router as commodities_router
from api.commodity_match import router as commodity_match_router
from api.faq import router as faq_router
from api.logistics import router as logistics_router
from api.materials import router as materials_router
from api.me import router as me_router
from api.profile import router as profile_router
from api.recommend import router as recommend_router
from api.reports import router as reports_router
from core.config import get_settings
from engine.commodity_matcher import load_model_and_embeddings
from engine.faq_matcher import load_faq_embeddings
from engine.ml_ranker import is_available as warm_ml_ranker

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Every model this app serves is paid for once here, at boot, instead of
    # on whichever request happens to be first — that first caller (or an
    # uptime pinger hitting /health) would otherwise eat a multi-second
    # model-load/embedding delay. Uvicorn does not start accepting
    # connections until this generator reaches `yield`, so /health cannot
    # respond "ok" before all three are warm.
    load_model_and_embeddings()
    load_faq_embeddings()
    warm_ml_ranker()
    yield


app = FastAPI(
    title="Wrapture",
    description="AI food packaging recommendation system (SIH PS 26236).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend_router)
app.include_router(me_router)
app.include_router(reports_router)
app.include_router(profile_router)
app.include_router(commodities_router)
app.include_router(commodity_match_router)
app.include_router(logistics_router)
app.include_router(materials_router)
app.include_router(faq_router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
