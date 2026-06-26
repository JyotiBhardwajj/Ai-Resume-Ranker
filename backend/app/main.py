from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="India Runs Hackathon Backend API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

from backend.app.api.routers.jd_router import router as jd_router
from backend.app.api.routers.candidate_router import router as candidate_router

app.include_router(jd_router, prefix="/api/jd", tags=["Job Descriptions"])
app.include_router(candidate_router, prefix="/api/candidates", tags=["Candidates"])

