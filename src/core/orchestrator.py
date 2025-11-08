"""
Main Orchestration Engine
Coordinates the three LLM modules and MCP tool execution
Implements the core penetration testing workflow
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .session import Session, PentestPhase, Task, TaskStatus, Vulnerability, Finding
from .config import config
from ..modules.reasoning import ReasoningModule
from ..modules.generation import GenerationModule
from ..modules.parsing import ParsingModule
from ..mcp.nmap_server import NmapMCPServer
from ..mcp.nikto_server import NiktoMCPServer
from ..mcp.sqlmap_server import SQLMapMCPServer
from ..mcp.gobuster_server import GobusterMCPServer
from ..agents import ReconAgent, EnumAgent, VulnAgent, ExploitAgent, ReportAgent
from ..orchestrator.chatbot_manager import ChatbotManager
from ..utils.logger import get_logger


class Orchestrator:
    """
    Main orchestration engine that coordinates:
    1. Three LLM modules (Reasoning, Generation, Parsing)
    2. MCP tool execution layer
    3. Session state management
    4. Workflow progression
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # Initialize LLM modules
        self.reasoning = ReasoningModule()
        self.generation = GenerationModule()
        self.parsing = ParsingModule()

        # Initialize MCP tool servers
        self.tools = {
            'nmap': NmapMCPServer(),
            'nikto': NiktoMCPServer(),
            'sqlmap': SQLMapMCPServer(),
            'gobuster': GobusterMCPServer(),
        }

        # Initialize agents
        self.recon_agent = ReconAgent(self)
        self.enum_agent = EnumAgent(self)
        self.vuln_agent = VulnAgent(self)
        self.exploit_agent = ExploitAgent(self)
        self.report_agent = ReportAgent(self)

        # Initialize chatbot manager
        self.chatbot_manager = ChatbotManager(self)

        # Active sessions
        self.sessions: Dict[str, Session] = {}

        # Workflow control
        self.running_sessions: Dict[str, bool] = {}

        self.logger.info("Orchestrator initialized with 3 modules, 5 agents, chatbot, and 4 MCP tools")

    async def start_pentest(
        self,
        target: str,
        scope: List[str],
        authorized: bool = False
    ) -> Session:
        """
        Initialize a new penetration test session

        Args:
            target: Target domain/IP address
            scope: List of testing scopes (e.g., ["network", "web"])
            authorized: Whether testing is authorized

        Returns:
            Initialized Session object
        """
        self.logger.info(f"Starting new pentest for target: {target}")

        # Validate target authorization
        if not authorized and config.security.require_target_approval:
            if not config.is_target_allowed(target):
                raise ValueError(
                    f"Target {target} is not in the approved list. "
                    f"Set authorized=True if you have permission."
                )

        # Create new session
        session = Session(
            target=target,
            scope=scope,
            authorized=authorized,
            status="active"
        )
        session.started_at = datetime.utcnow()

        # Store session
        self.sessions[session.session_id] = session

        # Save to disk
        session.save()

        self.logger.info(f"Created session: {session.session_id}")

        # Generate initial tasks using Reasoning module
        try:
            initial_tasks = await self.reasoning.plan_initial_tasks(session)
            session.add_tasks(initial_tasks)
            self.logger.info(f"Generated {len(initial_tasks)} initial tasks")
        except Exception as e:
            self.logger.error(f"Failed to generate initial tasks: {e}")
            # Add fallback default tasks
            session.add_task(Task(
                description="Perform initial network reconnaissance",
                tool="nmap",
                phase=PentestPhase.RECONNAISSANCE,
                priority=1
            ))

        session.save()

        return session

    async def execute_workflow(self, session_id: str, max_iterations: int = 50) -> Session:
        """
        Execute the main penetration testing workflow

        This is the core orchestration loop that:
        1. Uses Reasoning module to plan next steps
        2. Uses Generation module to create commands
        3. Executes commands via MCP tools
        4. Uses Parsing module to interpret results
        5. Updates session and repeats

        Args:
            session_id: ID of the session to execute
            max_iterations: Maximum number of workflow iterations (safety limit)

        Returns:
            Updated Session object
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        self.logger.info(f"Starting workflow execution for session: {session_id}")
        self.running_sessions[session_id] = True

        iteration = 0

        try:
            while (iteration < max_iterations and
                   self.running_sessions.get(session_id, False) and
                   session.current_phase != PentestPhase.COMPLETED):

                iteration += 1
                self.logger.info(f"=== Workflow Iteration {iteration} ===")
                self.logger.info(f"Phase: {session.current_phase.value}, Progress: {session.progress:.1f}%")

                # Check if we should advance phase
                if session.can_advance_phase():
                    should_advance = await self.reasoning.should_escalate_phase(session)
                    if should_advance:
                        session.advance_phase()
                        self.logger.info(f"Advanced to phase: {session.current_phase.value}")

                        if session.current_phase == PentestPhase.COMPLETED:
                            break

                        # Generate tasks for new phase
                        new_tasks = await self.reasoning.plan_next_steps(session)
                        session.add_tasks(new_tasks)
                        session.save()

                # Get next task to execute
                next_task = session.get_next_task()

                if not next_task:
                    # No pending tasks, ask reasoning module for more
                    self.logger.info("No pending tasks, requesting new tasks from Reasoning module")
                    new_tasks = await self.reasoning.plan_next_steps(session)

                    if not new_tasks:
                        # No more tasks and can't advance phase - we're done
                        self.logger.info("No more tasks available, completing session")
                        session.current_phase = PentestPhase.REPORTING
                        break

                    session.add_tasks(new_tasks)
                    next_task = session.get_next_task()

                if next_task:
                    await self._execute_task(session, next_task)
                    session.save()

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.5)

            # Generate final report
            if session.current_phase == PentestPhase.REPORTING or iteration >= max_iterations:
                self.logger.info("Entering reporting phase")
                session.current_phase = PentestPhase.REPORTING
                await self._generate_final_report(session)
                session.current_phase = PentestPhase.COMPLETED
                session.status = "completed"
                session.completed_at = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            session.status = "failed"
            session.metadata['error'] = str(e)
            raise

        finally:
            self.running_sessions[session_id] = False
            session.save()
            self.logger.info(f"Workflow execution completed for session: {session_id}")

        return session

    async def _execute_task(self, session: Session, task: Task) -> None:
        """
        Execute a single penetration testing task

        Workflow:
        1. Generate command using Generation module
        2. Execute command via appropriate MCP tool
        3. Parse output using Parsing module
        4. Update session with findings
        """
        self.logger.info(f"Executing task: {task.task_id} - {task.description}")
        task.start()

        try:
            # Step 1: Generate specific command using Generation module
            if not task.command and task.tool:
                self.logger.info(f"Generating command for tool: {task.tool}")
                command_info = await self.generation.generate_command(
                    tool=task.tool,
                    target=session.target,
                    context=session.get_context_summary(),
                    task_description=task.description
                )
                task.command = command_info.get('command')
                task.metadata = {
                    'explanation': command_info.get('explanation'),
                    'expected_output': command_info.get('expected_output')
                }

            # Step 2: Execute via MCP tool
            if task.tool and task.tool in self.tools:
                self.logger.info(f"Executing {task.tool} command: {task.command}")

                tool_server = self.tools[task.tool]
                result = await tool_server.execute({
                    'target': session.target,
                    'command': task.command,
                    'task_id': task.task_id
                })

                output = result.get('output', '')
                task.output = output

                # Step 3: Parse output using Parsing module
                if output:
                    self.logger.info(f"Parsing output from {task.tool}")
                    parsed_result = await self.parsing.parse_tool_output(
                        tool=task.tool,
                        output=output,
                        target=session.target
                    )

                    # Step 4: Extract and store findings
                    vulnerabilities = parsed_result.get('vulnerabilities', [])
                    findings = parsed_result.get('findings', [])

                    for vuln_data in vulnerabilities:
                        vuln = Vulnerability(**vuln_data)
                        session.add_vulnerability(vuln)
                        self.logger.info(f"Discovered vulnerability: {vuln.title} [{vuln.severity.value}]")

                    for finding_data in findings:
                        finding = Finding(**finding_data)
                        session.add_finding(finding)

                    # Update target info from findings
                    self._update_target_info(session, parsed_result)

                    # Complete task
                    session.complete_task(
                        task.task_id,
                        output=output,
                        findings_count=len(vulnerabilities) + len(findings)
                    )

                    self.logger.info(
                        f"Task completed: {len(vulnerabilities)} vulnerabilities, "
                        f"{len(findings)} findings"
                    )

                else:
                    session.complete_task(task.task_id, output="No output received", findings_count=0)

            else:
                # Manual task or tool not available
                self.logger.warning(f"Tool '{task.tool}' not available, marking task as completed")
                session.complete_task(task.task_id, output="Manual task - no tool execution", findings_count=0)

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}", exc_info=True)
            session.fail_task(task.task_id, error=str(e))

    def _update_target_info(self, session: Session, parsed_result: Dict[str, Any]) -> None:
        """Update session target info from parsed results"""
        target_info = session.target_info

        # Update IP addresses
        if 'ip_addresses' in parsed_result:
            for ip in parsed_result['ip_addresses']:
                if ip not in target_info.ip_addresses:
                    target_info.ip_addresses.append(ip)

        # Update open ports
        if 'open_ports' in parsed_result:
            for port in parsed_result['open_ports']:
                if port not in target_info.open_ports:
                    target_info.open_ports.append(port)

        # Update services
        if 'services' in parsed_result:
            target_info.services.update(parsed_result['services'])

        # Update technologies
        if 'technologies' in parsed_result:
            for tech in parsed_result['technologies']:
                if tech not in target_info.technologies:
                    target_info.technologies.append(tech)

        # Update OS
        if 'operating_system' in parsed_result and parsed_result['operating_system']:
            target_info.operating_system = parsed_result['operating_system']

        # Update web server
        if 'web_server' in parsed_result and parsed_result['web_server']:
            target_info.web_server = parsed_result['web_server']

    async def _generate_final_report(self, session: Session) -> None:
        """Generate comprehensive penetration test report"""
        self.logger.info("Generating final report")

        try:
            # Use Reasoning module to analyze overall findings
            analysis = await self.reasoning.analyze_findings(session)

            # Store analysis in session metadata
            session.metadata['final_analysis'] = analysis

            # Generate report using reporter utility
            from ..utils.reporter import generate_report
            report_path = await generate_report(session)

            session.metadata['report_path'] = str(report_path)
            self.logger.info(f"Report generated: {report_path}")

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            session.metadata['report_error'] = str(e)

    async def execute_single_task(self, session_id: str, task_id: str) -> Dict[str, Any]:
        """
        Execute a specific task by ID
        Useful for manual task execution via API

        Args:
            session_id: Session ID
            task_id: Task ID to execute

        Returns:
            Task execution result
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Find task
        task = None
        for t in session.todo_list:
            if t.task_id == task_id:
                task = t
                break

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Execute task
        await self._execute_task(session, task)
        session.save()

        return {
            'task_id': task.task_id,
            'status': task.status.value,
            'findings_count': task.findings_count,
            'output': task.output[:500] if task.output else None  # Truncate for API response
        }

    async def pause_session(self, session_id: str) -> None:
        """Pause an active penetration test session"""
        session = self.sessions.get(session_id)
        if session:
            self.running_sessions[session_id] = False
            session.status = "paused"
            session.save()
            self.logger.info(f"Session paused: {session_id}")

    async def resume_session(self, session_id: str) -> None:
        """Resume a paused penetration test session"""
        session = self.sessions.get(session_id)
        if session:
            session.status = "active"
            session.save()
            self.logger.info(f"Session resumed: {session_id}")
            # Resume workflow
            await self.execute_workflow(session_id)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try loading from disk
        try:
            session = Session.load(session_id)
            self.sessions[session_id] = session
            return session
        except FileNotFoundError:
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with basic info"""
        session_ids = set(self.sessions.keys()) | set(Session.list_sessions())

        sessions_info = []
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions_info.append({
                    'session_id': session.session_id,
                    'target': session.target,
                    'phase': session.current_phase.value,
                    'status': session.status,
                    'progress': session.progress,
                    'created_at': session.created_at.isoformat(),
                    'vulnerabilities_count': len(session.vulnerabilities)
                })

        return sessions_info

    async def generate_report(self, session_id: str) -> str:
        """
        Generate report for a session

        Args:
            session_id: Session ID

        Returns:
            Path to generated report
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        from ..utils.reporter import generate_report
        report_path = await generate_report(session)

        return str(report_path)

    async def cleanup(self) -> None:
        """Cleanup resources and save all sessions"""
        self.logger.info("Cleaning up orchestrator")

        # Stop all running sessions
        for session_id in list(self.running_sessions.keys()):
            self.running_sessions[session_id] = False

        # Save all sessions
        for session in self.sessions.values():
            try:
                session.save()
            except Exception as e:
                self.logger.error(f"Failed to save session {session.session_id}: {e}")

        self.logger.info("Orchestrator cleanup completed")
