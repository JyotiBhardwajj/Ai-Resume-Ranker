from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.ranking import router as ranking_router
from backend.api.candidates import router as candidates_router
from backend.api.jd import router as jd_router

# New API Routers
from backend.app.api.routers.candidate_router import router as candidate_app_router
from backend.app.api.routers.jd_router import router as jd_app_router


app = FastAPI(
    title="India Runs Candidate Ranking Service API",
    description="Backend service api for Candidate Discovery, Validation, Embedding and Ranking.",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base API Router
router = APIRouter()


@router.get("/", summary="Root status endpoint.")
def read_root() -> dict:
    """
    Returns the running status of the API server.
    """
    return {"status": "running"}


@router.get("/health", summary="Health check endpoint.")
def read_health() -> dict:
    """
    Returns health status of the application.
    """
    return {"health": "ok"}


# Include routers
app.include_router(router)
app.include_router(ranking_router)
app.include_router(candidates_router)
app.include_router(jd_router)

# Include new API Routers
app.include_router(candidate_app_router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(jd_app_router, prefix="/api/jd", tags=["Job Descriptions"])
