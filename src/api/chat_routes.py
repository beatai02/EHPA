"""
Chat API Routes
HTTP endpoints for chatbot interactions
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Chat message request"""
    message: str
    session_id: str = "default"
    user_id: str = "default_user"


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    response: str
    type: str
    suggestions: list = []
    data: Dict[str, Any] = {}
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    messages: list
    count: int


# Global orchestrator reference (set during startup)
_orchestrator = None


def set_orchestrator(orchestrator):
    """Set the global orchestrator reference"""
    global _orchestrator
    _orchestrator = orchestrator


# Routes

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Send a chat message to the AI assistant

    Args:
        request: Chat message request

    Returns:
        AI assistant response
    """
    if not _orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")

        # Process message through chatbot manager
        response = await _orchestrator.chatbot_manager.process_message(
            user_message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )

        return ChatMessageResponse(
            response=response.get('message', ''),
            type=response.get('type', 'text'),
            suggestions=response.get('suggestions', []),
            data=response.get('data', {}),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a session

    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return

    Returns:
        Chat history
    """
    if not _orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        # Get conversation context
        context = _orchestrator.chatbot_manager.context_manager.get_context(session_id)

        messages = context.get('messages', [])[-limit:]

        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            count=len(messages)
        )

    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a session

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    if not _orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        # Clear context
        _orchestrator.chatbot_manager.context_manager.clear_context(session_id)

        return {
            "message": "Chat history cleared",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error clearing chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/explain")
async def explain_concept(concept: str):
    """
    Explain a security concept

    Args:
        concept: Security concept to explain

    Returns:
        Explanation
    """
    if not _orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    try:
        # Use explainer to generate explanation
        explanation = await _orchestrator.chatbot_manager.conversation_handler.explainer.explain(concept)

        return {
            "concept": concept,
            "explanation": explanation,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error explaining concept: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/suggestions")
async def get_suggestions(context: str = "general"):
    """
    Get suggested chat prompts

    Args:
        context: Context for suggestions (general, scan_active, findings, etc.)

    Returns:
        List of suggested prompts
    """
    suggestions = {
        "general": [
            "Scan scanme.nmap.org",
            "What is SQL injection?",
            "Show me available tools",
            "Explain XSS vulnerabilities"
        ],
        "scan_active": [
            "Show current status",
            "What vulnerabilities have you found?",
            "Pause the scan",
            "Generate a report"
        ],
        "findings": [
            "Explain this vulnerability",
            "How do I fix this?",
            "Show remediation steps",
            "What's the risk?"
        ],
        "completed": [
            "Generate final report",
            "Show all critical findings",
            "Start a new scan",
            "Export results"
        ]
    }

    return {
        "context": context,
        "suggestions": suggestions.get(context, suggestions["general"])
    }


@router.get("/health")
async def chat_health():
    """
    Chat service health check

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "chat",
        "orchestrator_available": _orchestrator is not None,
        "timestamp": datetime.utcnow().isoformat()
    }
