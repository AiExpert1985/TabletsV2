"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from core.database import init_db
from core.config import get_settings
from core.exceptions import AppException
from features.auth.routes import router as auth_router
from features.company.routes import router as company_router
# Import models to ensure they're registered with SQLAlchemy
from features.company.models import Company  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    print("Starting up application...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for AppException
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


# Global exception handler for validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed logging."""
    # Log validation errors for debugging
    print(f"\n[VALIDATION ERROR] Path: {request.url.path}")
    print(f"[VALIDATION ERROR] Method: {request.method}")
    print(f"[VALIDATION ERROR] Errors:")
    for error in exc.errors():
        print(f"  - Field: {error['loc']}, Error: {error['msg']}, Type: {error['type']}")

    # Log request body if available
    try:
        body = await request.body()
        print(f"[VALIDATION ERROR] Request body: {body.decode()}")
    except Exception as e:
        print(f"[VALIDATION ERROR] Could not read request body: {e}")

    # Return standard 422 response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# Include routers
app.include_router(auth_router)
app.include_router(company_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
