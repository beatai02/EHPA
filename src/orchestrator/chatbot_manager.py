"""
Chatbot Manager - Main chatbot controller for orchestrator
Integrates chatbot with penetration testing workflow
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio

from ..chatbot.conversation_handler import ConversationHandler
from ..chatbot.command_parser import CommandParser
from ..chatbot.response_generator import ResponseGenerator
from ..chatbot.context_manager import ContextManager
from ..utils.logger import get_logger


class ChatbotManager:
    """
    Manages chatbot interactions and integrates with orchestrator

    Responsibilities:
    - Process user chat messages
    - Execute commands via orchestrator
    - Provide real-time updates
    - Generate educational responses
    """

    def __init__(self, orchestrator):
        """
        Initialize ChatbotManager

        Args:
            orchestrator: Reference to main Orchestrator instance
        """
        self.logger = get_logger(__name__)
        self.orchestrator = orchestrator

        # Initialize conversation handler
        self.conversation_handler = ConversationHandler()
        self.command_parser = CommandParser()
        self.response_generator = ResponseGenerator()
        self.context_manager = ContextManager()

        # Track active conversations
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        self.logger.info("ChatbotManager initialized")

    async def process_message(
        self,
        user_message: str,
        session_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Process user message and generate intelligent response

        This is the main entry point for chatbot interactions.

        Args:
            user_message: User's text message
            session_id: Penetration test session ID
            user_id: User identifier

        Returns:
            Response dictionary with:
                - response: Bot's text response
                - type: Response type (command, explanation, question, etc.)
                - data: Additional data
                - suggestions: List of suggested next actions
        """
        self.logger.info(f"Processing message for session {session_id}: {user_message[:50]}...")

        try:
            # Get session object if exists
            session_obj = self.orchestrator.get_session(session_id)

            # Handle message through conversation handler
            response = await self.conversation_handler.handle_message(
                message=user_message,
                session_id=session_id,
                user_id=user_id,
                session_obj=session_obj
            )

            # Check if response requires command execution
            if response.get('type') == 'command_intent':
                # Execute command and get result
                execution_result = await self._execute_command(
                    response.get('data', {}).get('intent', {}),
                    session_id
                )

                # Merge execution result with response
                if execution_result:
                    response['message'] += f"\n\n{execution_result['message']}"
                    response['data']['execution'] = execution_result
                    response['suggestions'] = execution_result.get('suggestions', response['suggestions'])

            return response

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return self.response_generator.format_error(
                error_message=str(e),
                explanation="I encountered an error processing your message.",
                suggestions=["Try again", "Rephrase your request", "Type 'help'"]
            )

    async def _execute_command(
        self,
        intent: Dict[str, Any],
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a command based on parsed intent

        Args:
            intent: Parsed intent with entities
            session_id: Session ID

        Returns:
            Execution result dictionary or None
        """
        entities = intent.get('entities', {})
        action = entities.get('action', 'unknown')
        target = entities.get('target')
        tool = entities.get('tool')

        self.logger.info(f"Executing command: action={action}, target={target}, tool={tool}")

        try:
            if action == 'scan' and target:
                return await self._execute_scan(target, session_id)

            elif action == 'run_tool' and tool:
                return await self._execute_tool(tool, target or session_id, session_id)

            elif action == 'show':
                return await self._show_results(session_id)

            elif action == 'report':
                return await self._generate_report(session_id)

            elif action == 'stop':
                return await self._stop_session(session_id)

            else:
                return {
                    'message': f"I understand you want to perform action: {action}, but I need more information.",
                    'suggestions': ["Be more specific", "Try 'scan <target>'", "Type 'help'"]
                }

        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {
                'message': f"� Failed to execute command: {str(e)}",
                'suggestions': ["Try again", "Check target", "View help"]
            }

    async def _execute_scan(self, target: str, session_id: str) -> Dict[str, Any]:
        """Execute a scan command"""
        try:
            # Check if session exists
            session = self.orchestrator.get_session(session_id)

            if not session:
                # Create new session
                session = await self.orchestrator.start_pentest(
                    target=target,
                    scope=["network", "web"],
                    authorized=False  # Will check against allowed targets
                )

                # Start workflow in background
                asyncio.create_task(self.orchestrator.execute_workflow(session.session_id))

                return self.response_generator.format_scan_started(
                    scan_type="Comprehensive",
                    target=target,
                    tool="multiple tools",
                    phase=session.current_phase.value,
                    estimated_duration="10-15 minutes"
                )
            else:
                # Session already exists
                return {
                    'message': f" Session already active for {session.target}\n\nCurrent phase: {session.current_phase.value}\nProgress: {session.progress}%",
                    'suggestions': ["Show status", "Show findings", "Continue scan"]
                }

        except ValueError as e:
            # Target not authorized
            return {
                'message': f"� Target Authorization Required\n\n{str(e)}\n\nPlease use an authorized test target like:\n- scanme.nmap.org\n- testphp.vulnweb.com",
                'suggestions': ["Scan scanme.nmap.org", "View allowed targets", "Help"]
            }

    async def _execute_tool(self, tool: str, target: str, session_id: str) -> Dict[str, Any]:
        """Execute a specific tool"""
        try:
            session = self.orchestrator.get_session(session_id)

            if not session:
                return {
                    'message': "� No active session. Start a scan first!",
                    'suggestions': [f"Scan {target}", "Help"]
                }

            # Create a task for the tool
            from ..core.session import Task, PentestPhase

            task = Task(
                description=f"Run {tool} on {target}",
                tool=tool,
                priority=1,
                phase=session.current_phase
            )

            session.add_task(task)
            session.save()

            # Execute the task
            result = await self.orchestrator.execute_single_task(session_id, task.task_id)

            return self.response_generator.format_scan_started(
                scan_type=f"{tool.upper()}",
                target=target,
                tool=tool,
                phase=session.current_phase.value
            )

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {
                'message': f"� Failed to run {tool}: {str(e)}",
                'suggestions': ["Try different tool", "Show available tools", "Help"]
            }

    async def _show_results(self, session_id: str) -> Dict[str, Any]:
        """Show current results"""
        session = self.orchestrator.get_session(session_id)

        if not session:
            return {
                'message': "No active session found. Start a scan first!",
                'suggestions': ["Start a scan", "Help"]
            }

        # Build session data
        session_data = {
            'target': session.target,
            'phase': session.current_phase.value.replace('_', ' ').title(),
            'progress': session.progress,
            'critical_count': len([v for v in session.vulnerabilities if v.severity.value == 'critical']),
            'high_count': len([v for v in session.vulnerabilities if v.severity.value == 'high']),
            'medium_count': len([v for v in session.vulnerabilities if v.severity.value == 'medium']),
            'low_count': len([v for v in session.vulnerabilities if v.severity.value == 'low']),
            'info_count': len([v for v in session.vulnerabilities if v.severity.value == 'informational']),
            'vulnerabilities': [v.model_dump() for v in session.vulnerabilities]
        }

        return self.response_generator.format_results_summary(session_data)

    async def _generate_report(self, session_id: str) -> Dict[str, Any]:
        """Generate penetration test report"""
        try:
            report_path = await self.orchestrator.generate_report(session_id)

            return {
                'message': f" Report Generated Successfully!\n\nReport saved to:\n`{report_path}`\n\nThe report includes:\n- Executive summary\n- All discovered vulnerabilities\n- Technical details\n- Remediation recommendations",
                'suggestions': ["View findings", "Start new scan", "Explain vulnerabilities"]
            }

        except Exception as e:
            return {
                'message': f"� Report generation failed: {str(e)}",
                'suggestions': ["Try again", "Check session status"]
            }

    async def _stop_session(self, session_id: str) -> Dict[str, Any]:
        """Stop/pause current session"""
        try:
            await self.orchestrator.pause_session(session_id)

            return {
                'message': "� Session paused successfully.\n\nYou can resume anytime with 'resume scan'.",
                'suggestions': ["Resume scan", "Show results so far", "Generate report"]
            }

        except Exception as e:
            return {
                'message': f"� Failed to pause session: {str(e)}",
                'suggestions': ["Try again"]
            }

    async def send_progress_update(
        self,
        session_id: str,
        progress: float,
        current_task: str,
        latest_finding: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send progress update (called by orchestrator during scan)

        Args:
            session_id: Session ID
            progress: Progress percentage
            current_task: Current task description
            latest_finding: Latest discovery

        Returns:
            Progress update message
        """
        session = self.orchestrator.get_session(session_id)
        if not session:
            return {}

        return self.response_generator.format_progress_update(
            progress=progress,
            current_task=current_task,
            completed_count=len(session.completed_tasks),
            total_count=len(session.todo_list) + len(session.completed_tasks),
            latest_finding=latest_finding
        )

    async def notify_vulnerability_found(
        self,
        session_id: str,
        vulnerability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Notify user of vulnerability discovery (called by orchestrator)

        Args:
            session_id: Session ID
            vulnerability: Vulnerability data

        Returns:
            Vulnerability notification message
        """
        return self.response_generator.format_vulnerability_found(vulnerability)

    async def notify_phase_complete(
        self,
        session_id: str,
        phase: str,
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Notify user of phase completion (called by orchestrator)

        Args:
            session_id: Session ID
            phase: Completed phase
            summary: Phase summary data

        Returns:
            Phase completion message
        """
        return self.response_generator.format_phase_complete(phase, summary)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        session = self.orchestrator.get_session(session_id)

        if not session:
            return None

        return {
            'session_id': session.session_id,
            'target': session.target,
            'phase': session.current_phase.value,
            'progress': session.progress,
            'status': session.status,
            'vulnerabilities_count': len(session.vulnerabilities),
            'created_at': session.created_at.isoformat()
        }

    def list_available_tools(self) -> List[str]:
        """List all available penetration testing tools"""
        return list(self.orchestrator.tools.keys())

    async def get_help(self) -> Dict[str, Any]:
        """Get help message"""
        return self.response_generator.format_help()
