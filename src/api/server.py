"""
FastAPI REST API Server
Provides HTTP endpoints for the orchestration system
This API will be consumed by the dashboard in Task 2
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.orchestrator import Orchestrator
from ..core.config import config
from ..utils.logger import get_logger
from .server_extensions import initialize_extensions
from .models import (
    PentestStartRequest, PentestStartResponse,
    SessionStatusResponse, FindingsResponse,
    SessionListResponse, TaskExecutionResponse,
    ReportResponse, ErrorResponse, HealthCheckResponse,
    StatisticsResponse, ExecuteTaskRequest, TaskInfo
)

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EHPA Task 1 - Backend Orchestration API",
    description="LLM-powered penetration testing orchestration system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for future dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[Orchestrator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator

    logger.info("Starting EHPA Backend Orchestration API")

    # Validate configuration
    is_valid, errors = config.validate_config()
    if not is_valid:
        logger.warning(f"Configuration warnings: {errors}")

    # Initialize orchestrator
    orchestrator = Orchestrator()

    # Initialize server extensions (WebSocket, static files, chat routes, OSINT routes)
    initialize_extensions(app, orchestrator)

    logger.info("API server initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator

    logger.info("Shutting down EHPA Backend Orchestration API")

    if orchestrator:
        await orchestrator.cleanup()

    logger.info("API server shutdown complete")


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "EHPA Task 1 - Backend Orchestration API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthCheckResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "orchestrator": "running" if orchestrator else "not initialized",
            "llm_reasoning": "available",
            "llm_generation": "available",
            "llm_parsing": "available",
            "mcp_tools": "4 tools available"
        }
    )


@app.post(
    "/api/v1/pentest/start",
    response_model=PentestStartResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Penetration Testing"]
)
async def start_pentest(
    request: PentestStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new penetration test session

    This endpoint:
    1. Creates a new session
    2. Validates target authorization
    3. Generates initial tasks using Reasoning module
    4. Optionally starts automated workflow in background

    Returns session information
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    logger.info(f"Starting pentest for target: {request.target}")

    try:
        # Start penetration test session
        session = await orchestrator.start_pentest(
            target=request.target,
            scope=request.scope,
            authorized=request.authorized
        )

        # Note: Workflow execution can be started here or triggered separately
        # For now, we'll let the user manually control workflow execution
        # background_tasks.add_task(orchestrator.execute_workflow, session.session_id)

        return PentestStartResponse(
            session_id=session.session_id,
            target=session.target,
            status=session.status,
            current_phase=session.current_phase.value,
            created_at=session.created_at,
            message=f"Penetration test session created. Use /api/v1/pentest/{session.session_id}/execute to start workflow."
        )

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to start pentest: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to start pentest: {str(e)}")


@app.post(
    "/api/v1/pentest/{session_id}/execute",
    tags=["Penetration Testing"]
)
async def execute_workflow(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start automated workflow execution for a session

    Runs the main orchestration loop in the background
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    # Start workflow in background
    background_tasks.add_task(orchestrator.execute_workflow, session_id)

    return {
        "session_id": session_id,
        "message": "Workflow execution started in background",
        "status": "running"
    }


@app.get(
    "/api/v1/pentest/{session_id}/status",
    response_model=SessionStatusResponse,
    tags=["Penetration Testing"]
)
async def get_session_status(session_id: str):
    """
    Get current status of a penetration test session

    Returns:
    - Current phase
    - Progress percentage
    - Task counts
    - Findings count
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    # Get current task
    current_task = None
    if session.todo_list:
        in_progress_tasks = [t for t in session.todo_list if t.status == "in_progress"]
        if in_progress_tasks:
            current_task = in_progress_tasks[0].description

    return SessionStatusResponse(
        session_id=session.session_id,
        target=session.target,
        phase=session.current_phase.value,
        status=session.status,
        progress=session.progress,
        current_task=current_task,
        tasks_pending=len(session.todo_list),
        tasks_completed=len(session.completed_tasks),
        findings_count=len(session.findings),
        vulnerabilities_count=len(session.vulnerabilities),
        duration_minutes=session.get_duration_minutes()
    )


@app.get(
    "/api/v1/pentest/{session_id}/statistics",
    response_model=StatisticsResponse,
    tags=["Penetration Testing"]
)
async def get_session_statistics(session_id: str):
    """Get detailed session statistics"""
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    stats = session.get_statistics()

    return StatisticsResponse(**stats)


@app.get(
    "/api/v1/pentest/{session_id}/findings",
    response_model=FindingsResponse,
    tags=["Penetration Testing"]
)
async def get_session_findings(session_id: str):
    """
    Get all discovered vulnerabilities and findings

    Returns vulnerabilities categorized by severity
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    # Categorize vulnerabilities by severity
    from ..core.session import SeverityLevel

    vulnerabilities_by_severity = {
        'critical': session.get_vulnerabilities_by_severity(SeverityLevel.CRITICAL),
        'high': session.get_vulnerabilities_by_severity(SeverityLevel.HIGH),
        'medium': session.get_vulnerabilities_by_severity(SeverityLevel.MEDIUM),
        'low': session.get_vulnerabilities_by_severity(SeverityLevel.LOW),
        'informational': session.get_vulnerabilities_by_severity(SeverityLevel.INFORMATIONAL)
    }

    # Convert to dict format
    vulnerabilities_list = []
    for vuln in session.vulnerabilities:
        vulnerabilities_list.append(vuln.model_dump())

    return FindingsResponse(
        session_id=session.session_id,
        total_vulnerabilities=len(session.vulnerabilities),
        critical=len(vulnerabilities_by_severity['critical']),
        high=len(vulnerabilities_by_severity['high']),
        medium=len(vulnerabilities_by_severity['medium']),
        low=len(vulnerabilities_by_severity['low']),
        informational=len(vulnerabilities_by_severity['informational']),
        vulnerabilities=vulnerabilities_list,
        general_findings=len(session.findings)
    )


@app.get(
    "/api/v1/pentest/{session_id}/tasks",
    tags=["Penetration Testing"]
)
async def get_session_tasks(session_id: str):
    """
    Get all tasks (pending, in progress, and completed)
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    tasks = {
        "pending": [t.model_dump() for t in session.todo_list],
        "completed": [t.model_dump() for t in session.completed_tasks],
        "failed": [t.model_dump() for t in session.failed_tasks]
    }

    return {
        "session_id": session.session_id,
        "tasks": tasks,
        "total_pending": len(session.todo_list),
        "total_completed": len(session.completed_tasks),
        "total_failed": len(session.failed_tasks)
    }


@app.post(
    "/api/v1/pentest/{session_id}/execute-task",
    response_model=TaskExecutionResponse,
    tags=["Penetration Testing"]
)
async def execute_single_task(
    session_id: str,
    request: ExecuteTaskRequest
):
    """
    Execute a specific task by ID

    Useful for manual control of the penetration test workflow
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    try:
        result = await orchestrator.execute_single_task(session_id, request.task_id)

        return TaskExecutionResponse(
            task_id=result['task_id'],
            status=result['status'],
            findings_count=result['findings_count'],
            output_preview=result.get('output'),
            message=f"Task {result['task_id']} executed successfully"
        )

    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        raise HTTPException(500, f"Task execution failed: {str(e)}")


@app.post(
    "/api/v1/pentest/{session_id}/pause",
    tags=["Penetration Testing"]
)
async def pause_session(session_id: str):
    """Pause an active penetration test session"""
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    await orchestrator.pause_session(session_id)

    return {
        "session_id": session_id,
        "status": "paused",
        "message": "Session paused successfully"
    }


@app.post(
    "/api/v1/pentest/{session_id}/resume",
    tags=["Penetration Testing"],
    description="Resume a paused session and continue workflow"
)
async def resume_session(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """Resume a paused penetration test session"""
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    # Resume in background
    background_tasks.add_task(orchestrator.resume_session, session_id)

    return {
        "session_id": session_id,
        "status": "resuming",
        "message": "Session resume initiated"
    }


@app.get(
    "/api/v1/pentest/{session_id}/report",
    response_model=ReportResponse,
    tags=["Penetration Testing"]
)
async def generate_report(session_id: str):
    """
    Generate comprehensive penetration test report

    Returns path to the generated report
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    try:
        report_path = await orchestrator.generate_report(session_id)

        return ReportResponse(
            session_id=session_id,
            report_path=report_path,
            generated_at=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(500, f"Report generation failed: {str(e)}")


@app.get(
    "/api/v1/pentest/sessions",
    response_model=SessionListResponse,
    tags=["Penetration Testing"]
)
async def list_sessions():
    """
    List all penetration test sessions

    Returns summary information for all sessions
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    sessions = orchestrator.list_sessions()

    return SessionListResponse(
        sessions=sessions,
        total=len(sessions)
    )


@app.delete(
    "/api/v1/pentest/{session_id}",
    tags=["Penetration Testing"]
)
async def delete_session(session_id: str):
    """
    Delete a penetration test session

    Note: This is a soft delete - files remain on disk
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session not found: {session_id}")

    # Remove from active sessions
    if session_id in orchestrator.sessions:
        del orchestrator.sessions[session_id]

    return {
        "session_id": session_id,
        "message": "Session deleted successfully"
    }


@app.get(
    "/api/v1/config",
    tags=["Configuration"]
)
async def get_configuration():
    """Get current system configuration (non-sensitive)"""
    return {
        "llm": {
            "model": config.llm.model,
            "max_tokens": config.llm.max_tokens,
            "temperature": config.llm.temperature
        },
        "security": {
            "require_target_approval": config.security.require_target_approval,
            "max_concurrent_scans": config.security.max_concurrent_scans
        },
        "tools": {
            "nmap": "available",
            "nikto": "available",
            "sqlmap": "available",
            "gobuster": "available"
        }
    }


@app.get(
    "/api/v1/tools",
    tags=["Tools"]
)
async def list_tools():
    """List available pentesting tools"""
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")

    tools_info = []
    for tool_name, tool_server in orchestrator.tools.items():
        tools_info.append(tool_server.get_info())

    return {
        "tools": tools_info,
        "total": len(tools_info)
    }


# Websocket endpoint for real-time updates (optional - for future enhancement)
# from fastapi import WebSocket
# @app.websocket("/api/v1/pentest/{session_id}/ws")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     """WebSocket endpoint for real-time session updates"""
#     await websocket.accept()
#     # Implementation for real-time updates
#     pass
