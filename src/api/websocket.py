"""
WebSocket Server for Real-time Chat
Provides real-time bidirectional communication for the chatbot
"""

import asyncio
import logging
import json
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication
    """

    def __init__(self):
        # Active connections: {session_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata: {websocket_id: metadata}
        self.connection_metadata: Dict[int, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str = "default"):
        """
        Accept new WebSocket connection

        Args:
            websocket: WebSocket instance
            session_id: Session identifier
        """
        await websocket.accept()

        # Add to active connections
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

        # Store metadata
        self.connection_metadata[id(websocket)] = {
            'session_id': session_id,
            'connected_at': datetime.utcnow(),
            'user_agent': websocket.headers.get('user-agent', 'Unknown')
        }

        logger.info(f"WebSocket connected: session={session_id}, total={len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket instance
        """
        ws_id = id(websocket)

        if ws_id in self.connection_metadata:
            session_id = self.connection_metadata[ws_id]['session_id']

            # Remove from active connections
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)

                # Clean up empty session
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

            # Remove metadata
            del self.connection_metadata[ws_id]

            logger.info(f"WebSocket disconnected: session={session_id}")

    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """
        Send message to specific websocket

        Args:
            message: Message dictionary
            websocket: Target WebSocket
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send personal message: {e}")

    async def send_to_session(self, message: Dict, session_id: str):
        """
        Send message to all connections in a session

        Args:
            message: Message dictionary
            session_id: Target session
        """
        if session_id not in self.active_connections:
            return

        dead_connections = []

        for connection in self.active_connections[session_id]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    dead_connections.append(connection)
            except Exception as e:
                logger.error(f"Failed to send to session {session_id}: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

    async def broadcast(self, message: Dict):
        """
        Broadcast message to all active connections

        Args:
            message: Message dictionary
        """
        dead_connections = []

        for session_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                    else:
                        dead_connections.append((session_id, connection))
                except Exception as e:
                    logger.error(f"Failed to broadcast: {e}")
                    dead_connections.append((session_id, connection))

        # Clean up dead connections
        for session_id, conn in dead_connections:
            self.disconnect(conn)

    def get_session_count(self, session_id: str) -> int:
        """Get number of connections for a session"""
        return len(self.active_connections.get(session_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            'total_connections': self.get_total_connections(),
            'active_sessions': len(self.active_connections),
            'sessions': {
                session_id: len(connections)
                for session_id, connections in self.active_connections.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator,
    session_id: str = "default"
):
    """
    WebSocket endpoint handler

    Args:
        websocket: WebSocket connection
        orchestrator: Main orchestrator instance
        session_id: Session identifier
    """
    await manager.connect(websocket, session_id)

    try:
        # Send welcome message
        await manager.send_personal_message({
            'type': 'welcome',
            'message': 'Connected to EHPA WebSocket',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)

        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }, websocket)
                continue

            # Handle message
            response = await handle_websocket_message(
                message,
                session_id,
                orchestrator
            )

            # Send response
            if response:
                await manager.send_personal_message(response, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected: session={session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


async def handle_websocket_message(
    message: Dict,
    session_id: str,
    orchestrator
) -> Dict:
    """
    Handle incoming WebSocket message

    Args:
        message: Message dictionary
        session_id: Session identifier
        orchestrator: Main orchestrator instance

    Returns:
        Response dictionary
    """
    message_type = message.get('type', 'unknown')

    try:
        if message_type == 'chat':
            # Chat message - process through chatbot
            user_message = message.get('message', '')

            if not user_message:
                return {
                    'type': 'error',
                    'message': 'Empty message'
                }

            # Process through chatbot manager
            response = await orchestrator.chatbot_manager.process_message(
                user_message=user_message,
                session_id=session_id,
                user_id=message.get('user_id', 'default_user')
            )

            return {
                'type': 'chat_response',
                'data': response,
                'timestamp': datetime.utcnow().isoformat()
            }

        elif message_type == 'ping':
            # Heartbeat
            return {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }

        elif message_type == 'status':
            # Request session status
            session = orchestrator.get_session(session_id)

            if not session:
                return {
                    'type': 'status',
                    'data': {'status': 'no_session'}
                }

            return {
                'type': 'status',
                'data': {
                    'session_id': session.session_id,
                    'target': session.target,
                    'phase': session.current_phase.value,
                    'progress': session.progress,
                    'status': session.status
                }
            }

        else:
            return {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
        return {
            'type': 'error',
            'message': str(e)
        }


async def broadcast_progress_update(
    session_id: str,
    progress: float,
    current_task: str,
    latest_finding: str = None
):
    """
    Broadcast progress update to all connections in a session

    Args:
        session_id: Session identifier
        progress: Progress percentage
        current_task: Current task description
        latest_finding: Latest finding (optional)
    """
    await manager.send_to_session({
        'type': 'progress',
        'data': {
            'progress': progress,
            'current_task': current_task,
            'latest_finding': latest_finding,
            'timestamp': datetime.utcnow().isoformat()
        }
    }, session_id)


async def broadcast_vulnerability_found(
    session_id: str,
    vulnerability: Dict
):
    """
    Broadcast vulnerability discovery

    Args:
        session_id: Session identifier
        vulnerability: Vulnerability data
    """
    await manager.send_to_session({
        'type': 'vulnerability_found',
        'data': vulnerability,
        'timestamp': datetime.utcnow().isoformat()
    }, session_id)


async def broadcast_phase_complete(
    session_id: str,
    phase: str,
    summary: Dict
):
    """
    Broadcast phase completion

    Args:
        session_id: Session identifier
        phase: Completed phase name
        summary: Phase summary
    """
    await manager.send_to_session({
        'type': 'phase_complete',
        'data': {
            'phase': phase,
            'summary': summary
        },
        'timestamp': datetime.utcnow().isoformat()
    }, session_id)


async def broadcast_scan_complete(
    session_id: str,
    results: Dict
):
    """
    Broadcast scan completion

    Args:
        session_id: Session identifier
        results: Final results
    """
    await manager.send_to_session({
        'type': 'scan_complete',
        'data': results,
        'timestamp': datetime.utcnow().isoformat()
    }, session_id)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return manager
