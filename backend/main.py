"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from core.database import init_db
from core.config import get_settings
from core.exceptions import AppException, PermissionDeniedException
from features.auth.auth_routes import router as auth_router
from features.users.routes import router as user_router
from features.company.routes import router as company_router
from features.product.routes import router as product_router
from features.audit.routes import router as audit_logs_router
from features.logging.logger import setup_logging, get_logger
from features.logging.middleware import LoggingMiddleware, ExceptionLoggingMiddleware
# Import models to ensure they're registered with SQLAlchemy
from features.users.models import User  # noqa: F401
from features.auth.models import RefreshToken  # noqa: F401
from features.company.models import Company  # noqa: F401
from features.product.models import Product  # noqa: F401
from features.audit.models import AuditLog  # noqa: F401

# Initialize logging FIRST (before anything else)
setup_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info("Starting up application...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add logging middleware (FIRST - outermost)
app.add_middleware(ExceptionLoggingMiddleware)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for PermissionDeniedException (403)
@app.exception_handler(PermissionDeniedException)
async def permission_denied_handler(request: Request, exc: PermissionDeniedException):
    """Handle authorization/permission exceptions."""
    logger.warning(
        f"PermissionDenied: {exc.message} | "
        f"Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


# Global exception handler for AppException (400)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions."""
    logger.warning(
        f"AppException: {exc.code} - {exc.message} | "
        f"Path: {request.url.path}"
    )
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
    # Log validation errors
    logger.warning(
        f"Validation Error | Path: {request.url.path} | "
        f"Errors: {exc.errors()}"
    )

    # Return standard 422 response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(company_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(audit_logs_router, prefix="/api")


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
        reload_excludes=["logs/*", "*.log"],  # Prevent log file feedback loop
    )
