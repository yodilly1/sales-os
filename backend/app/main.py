from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics

app = FastAPI(
    title="Sales OS API",
    description="API for Sales OS Analytics Dashboard",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sales-os-api"}
