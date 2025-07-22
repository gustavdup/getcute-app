"""
Main FastAPI application for the Cute WhatsApp Bot.
"""
import logging
import sys
import os
from typing import Optional
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.settings import settings
from config.database import db_manager
from handlers.webhook_handler import webhook_router
from handlers.slash_commands import commands_router
from utils.logger import setup_application_logging

# Configure comprehensive logging
setup_application_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cute WhatsApp Bot",
    description="A no-friction WhatsApp bot for brain-dumping and personal productivity",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="portal/static"), name="static")
templates = Jinja2Templates(directory="portal/templates")

# Import admin panel from admin folder
admin_path = Path(__file__).parent.parent / "admin"
sys.path.insert(0, str(admin_path))

# Include routers
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
app.include_router(commands_router, prefix="/api", tags=["commands"])

# Import admin router after path is set
try:
    from admin_panel import admin_router  # type: ignore
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    logger.info("Admin panel loaded successfully")
    
    # Also include the comprehensive user admin router with different prefix
    from user_admin import user_admin_router  # type: ignore
    app.include_router(user_admin_router, prefix="/admin/user", tags=["user-admin"])
    logger.info("User admin panel loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load admin panel: {e}")
    # Add a simple fallback admin endpoint
    @app.get("/admin")
    async def admin_fallback():
        return {"message": "Admin panel not available", "error": str(e)}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Cute WhatsApp Bot...")
    
    # Setup database
    await db_manager.setup_database()
    
    # Check database health
    if await db_manager.health_check():
        logger.info("Database connection established")
    else:
        logger.error("Database connection failed")
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down Cute WhatsApp Bot...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cute WhatsApp Bot is running! 🤖💚",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_healthy = await db_manager.health_check()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
    }


@app.get("/portal")
async def portal_dashboard(request: Request, token: Optional[str] = None):
    """Portal dashboard (would implement proper auth)."""
    # This is a placeholder - real implementation would:
    # 1. Validate the SSO token
    # 2. Extract user info
    # 3. Render dashboard with user data
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": {"name": "User", "phone": "+1234567890"}
    })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
