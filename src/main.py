"""StoreOps REST API main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.activities.routes import router as activities_router
from src.alerts.routes import router as alerts_router
from src.programmes.routes import router as programmes_router
from src.reports.routes import router as reports_router
from src.shared.errors import AppError
from src.staff.routes import router as staff_router

# Create FastAPI application
app = FastAPI(
    title="StoreOps API",
    description="Retail Operations Management REST API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):  # type: ignore
    """Handle AppError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "message": "StoreOps API is running"}


# Include routers from modules
app.include_router(activities_router)
app.include_router(programmes_router)
app.include_router(staff_router)
app.include_router(alerts_router)
app.include_router(reports_router)


@app.get("/api/v1")
async def api_root() -> dict:
    """API root endpoint with available modules."""
    return {
        "message": "StoreOps API v1",
        "modules": {
            "activities": "/api/v1/activities",
            "programmes": "/api/v1/programmes",
            "staff": "/api/v1/staff",
            "alerts": "/api/v1/alerts",
            "reports": "/api/v1/reports",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
