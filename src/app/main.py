"""
Doctor Onboarding Service - Main Application.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .api.v1 import router as v1_router
from .core.config import get_settings
from .core.exceptions import AppException
from .core.responses import ErrorDetail, ErrorResponse, ResponseMeta
from .db.session import close_db, init_db, get_db_manager

# Configure structured logging
def configure_logging() -> None:
    """Configure structured logging with structlog."""
    settings = get_settings()
    
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Also configure standard logging for third-party libraries
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=log_level,
        stream=sys.stdout,
    )

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, configure logging, start background tasks
    - Shutdown: Close database connections, cleanup sessions
    """
    import asyncio
    from .services.voice_service import get_voice_service
    
    settings = get_settings()
    logger = structlog.get_logger()
    
    # Background task for session cleanup
    cleanup_task: asyncio.Task | None = None
    
    async def periodic_session_cleanup() -> None:
        """Cleanup expired voice sessions every 5 minutes."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                voice_service = get_voice_service()
                cleaned = await voice_service.store.cleanup_expired()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired voice sessions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    

    # Startup
    logger.info(
        "Starting application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
    
    configure_logging()
    
    # Initialize PostgreSQL database
    db_manager = get_db_manager()
    await db_manager.create_tables()
    
    # Check database health
    health = await db_manager.health_check()
    logger.info("Database health check", postgres=health)
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_session_cleanup())
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Cancel background tasks
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
    # Close database connections
    await close_db()
    
    logger.info("Application shutdown complete")

def create_application() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application with:
    - CORS middleware
    - Exception handlers
    - API routers
    - OpenAPI documentation
    """
    settings = get_settings()
    
    # OpenAPI Tags metadata for better organization
    tags_metadata = [
        {
            "name": "Health",
            "description": "🏥 **Health Check & Readiness Probes** - Monitor service status and dependencies",
        },
        {
            "name": "Doctors",
            "description": "👨‍⚕️ **Doctor Management** - CRUD operations for doctor records including qualifications, practice locations, and professional details",
        },
        {
            "name": "Onboarding",
            "description": "📄 **AI-Powered Resume Extraction** - Upload resumes (PDF/Image) and automatically extract structured professional data using Google Gemini Vision",
        },
        {
            "name": "Voice Onboarding",
            "description": "🎤 **Voice-Based Registration** - Natural language conversation interface for collecting doctor information through speech",
        },
    ]
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
# 🏥 Doctor Onboarding Smart-Fill API

**Production-grade REST API** for doctor onboarding with AI-powered data extraction.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Extraction** | Upload PDF/Image resumes and extract structured data using Gemini AI Vision |
| 👨‍⚕️ **Doctor Management** | Full CRUD operations for doctor records with validation |
| 🎤 **Voice Onboarding** | Natural language conversation for hands-free data collection |
| 🔄 **Real-time Processing** | Fast AI-powered extraction with confidence scores |

---

## 🚀 Quick Start

### 1. Extract data from a resume
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/extract-resume \\
  -F "file=@doctor_resume.pdf"
```

### 2. Create a doctor record
```bash
curl -X POST http://localhost:8000/api/v1/doctors \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Dr. Smith", "email": "smith@hospital.com", ...}'
```

### 3. Start voice onboarding
```bash
curl -X POST http://localhost:8000/api/v1/voice/start \\
  -H "Content-Type: application/json" \\
  -d '{"language": "en"}'
```

---

## 📋 API Versioning

All endpoints are versioned under `/api/v1/` for backward compatibility.

## 🔐 Authentication

> ⚠️ **Note:** Authentication is disabled in development mode. Enable OAuth2 or API keys in production.

## 📊 Response Format

All responses follow a consistent structure:
```json
{
  "message": "Operation successful",
  "data": { ... },
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

---

Made with ❤️ for healthcare professionals
        """,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        openapi_tags=tags_metadata,
        swagger_ui_parameters={
            "docExpansion": "list",
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "syntaxHighlight.theme": "monokai",
            "tryItOutEnabled": True,
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        contact={
            "name": "API Support",
            "email": "support@example.com",
        },
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.cors_methods_list,
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include API routers
    app.include_router(v1_router)
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        """Root endpoint - API information."""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    
    return app

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    logger = structlog.get_logger()
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
        """Handle application-specific exceptions."""
        logger.warning(
            "Application exception",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url),
        )
        
        return ORJSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=exc.error_code,
                    message=exc.message,
                    details=exc.details,
                ),
                meta=ResponseMeta(),
            ).model_dump(),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> ORJSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            "Validation error",
            errors=exc.errors(),
            path=str(request.url),
        )
        
        # Format validation errors
        validation_errors = []
        for error in exc.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        return ORJSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details={"validation_errors": validation_errors},
                ),
                meta=ResponseMeta(),
            ).model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> ORJSONResponse:
        """Handle unexpected exceptions."""
        settings = get_settings()
        
        logger.exception(
            "Unhandled exception",
            error=str(exc),
            path=str(request.url),
        )
        
        # Don't expose internal errors in production
        message = str(exc) if settings.DEBUG else "An unexpected error occurred"
        
        return ORJSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message=message,
                ),
                meta=ResponseMeta(),
            ).model_dump(),
        )

# Create application instance
app = create_application()
