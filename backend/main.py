import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from config import settings
from db import MongoDB
from router import auth_router, sessions_router, documents_router, query_router, workflow_router


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Connect to MongoDB on startup
    - Disconnect from MongoDB on shutdown
    - Create necessary directories
    """
    logger.info("Starting up...")
    
    Path(settings.upload.directory).mkdir(parents=True, exist_ok=True)
    
    Path(settings.vectorstore.persist_directory).mkdir(parents=True, exist_ok=True)
    
    try:
        await MongoDB.connect()
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")
    await MongoDB.disconnect()
    logger.info("Disconnected from MongoDB")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""Backend for Agentic Multi Modal RAG Application""",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,  
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "error": "validation_error",
            "message": "Request validation failed",
            "details": {"errors": errors},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "internal_error",
            "message": "An internal error occurred",
            "details": {"error": str(exc)} if settings.debug else None,
        },
    )





app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(sessions_router, prefix=settings.api_prefix)
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(query_router, prefix=settings.api_prefix)
app.include_router(workflow_router, prefix=settings.api_prefix)




@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    """
    checks = {
        "mongodb": False,
    }
    
    try:
        db = MongoDB.get_database()
        await db.command("ping")
        checks["mongodb"] = True
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
        },
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "health": "/health",
    }

