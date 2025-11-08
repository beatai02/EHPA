"""
Server Extensions
Add WebSocket and static file serving to main API server
"""

import logging
from pathlib import Path
from fastapi import WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


def setup_static_files(app):
    """
    Mount static files and templates

    Args:
        app: FastAPI application instance
    """
    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Mount static files
    static_path = project_root / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info(f"Mounted static files from {static_path}")
    else:
        logger.warning(f"Static files directory not found: {static_path}")

    # Serve dashboard HTML
    templates_path = project_root / "web" / "templates"

    @app.get("/dashboard", response_class=HTMLResponse, tags=["Web UI"])
    async def serve_dashboard():
        """Serve main dashboard"""
        dashboard_path = templates_path / "dashboard.html"

        if not dashboard_path.exists():
            return HTMLResponse(
                content="<h1>Dashboard not found</h1><p>The dashboard.html file is missing.</p>",
                status_code=404
            )

        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

    @app.get("/", response_class=HTMLResponse, tags=["Web UI"])
    async def serve_root():
        """Redirect root to dashboard"""
        return HTMLResponse(
            content='<meta http-equiv="refresh" content="0; url=/dashboard">',
            status_code=302
        )

    logger.info("Static file serving configured")


def setup_websocket(app, orchestrator):
    """
    Setup WebSocket endpoint

    Args:
        app: FastAPI application instance
        orchestrator: Orchestrator instance
    """
    from .websocket import websocket_endpoint

    @app.websocket("/api/v1/chat/ws")
    async def websocket_chat(websocket: WebSocket, session_id: str = "default"):
        """
        WebSocket endpoint for real-time chat

        Args:
            websocket: WebSocket connection
            session_id: Session identifier
        """
        await websocket_endpoint(websocket, orchestrator, session_id)

    logger.info("WebSocket endpoint configured at /api/v1/chat/ws")


def setup_chat_routes(app, orchestrator):
    """
    Include chat API routes

    Args:
        app: FastAPI application instance
        orchestrator: Orchestrator instance
    """
    from .chat_routes import router, set_orchestrator

    # Set orchestrator reference for chat routes
    set_orchestrator(orchestrator)

    # Include router
    app.include_router(router)

    logger.info("Chat routes configured")


def setup_osint_routes(app, orchestrator):
    """
    Add OSINT API routes

    Args:
        app: FastAPI application instance
        orchestrator: Orchestrator instance
    """
    from fastapi import APIRouter

    router = APIRouter(prefix="/api/v1/osint", tags=["OSINT"])

    @router.get("/recent")
    async def get_recent_osint(category: str = None, hours: int = 24, limit: int = 50):
        """Get recent OSINT items"""
        try:
            # Get OSINT aggregator
            osint_aggregator = getattr(orchestrator, 'osint_aggregator', None)

            if not osint_aggregator:
                return {"items": [], "message": "OSINT aggregator not initialized"}

            items = osint_aggregator.get_recent_items(
                category=category,
                hours=hours,
                limit=limit
            )

            return {
                "items": items,
                "count": len(items),
                "category": category or "all",
                "hours": hours
            }

        except Exception as e:
            logger.error(f"Failed to get OSINT items: {e}")
            return {"items": [], "error": str(e)}

    @router.get("/search")
    async def search_osint(query: str, limit: int = 20):
        """Search OSINT items"""
        try:
            osint_aggregator = getattr(orchestrator, 'osint_aggregator', None)

            if not osint_aggregator:
                return {"items": [], "message": "OSINT aggregator not initialized"}

            items = osint_aggregator.search_items(query, limit)

            return {
                "items": items,
                "count": len(items),
                "query": query
            }

        except Exception as e:
            logger.error(f"Failed to search OSINT: {e}")
            return {"items": [], "error": str(e)}

    @router.get("/status")
    async def get_osint_status():
        """Get OSINT aggregator status"""
        try:
            osint_aggregator = getattr(orchestrator, 'osint_aggregator', None)

            if not osint_aggregator:
                return {"status": "not_initialized"}

            return osint_aggregator.get_statistics()

        except Exception as e:
            logger.error(f"Failed to get OSINT status: {e}")
            return {"status": "error", "error": str(e)}

    app.include_router(router)
    logger.info("OSINT routes configured")


def initialize_extensions(app, orchestrator):
    """
    Initialize all server extensions

    Args:
        app: FastAPI application instance
        orchestrator: Orchestrator instance
    """
    logger.info("Initializing server extensions...")

    # Setup static files and templates
    setup_static_files(app)

    # Setup WebSocket
    setup_websocket(app, orchestrator)

    # Setup chat routes
    setup_chat_routes(app, orchestrator)

    # Setup OSINT routes
    setup_osint_routes(app, orchestrator)

    logger.info("All server extensions initialized")
