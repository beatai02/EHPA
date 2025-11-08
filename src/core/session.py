"""
Session Management
Handles penetration test session state, tasks, findings, and context
Critical for preventing context loss between LLM interactions
"""

import uuid
import json
import asyncio
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class PentestPhase(str, Enum):
    """Penetration testing phases following PTES methodology"""
    RECONNAISSANCE = "reconnaissance"
    ENUMERATION = "enumeration"
    VULNERABILITY_SCANNING = "vulnerability_scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """Status of individual pentest tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Task(BaseModel):
    """Individual penetration testing task"""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str
    tool: Optional[str] = None
    command: Optional[str] = None
    phase: PentestPhase
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)  # 1=highest, 10=lowest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    findings_count: int = 0

    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, output: str, findings_count: int = 0) -> None:
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output = output
        self.findings_count = findings_count

    def fail(self, error: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Vulnerability(BaseModel):
    """Individual vulnerability finding"""
    vuln_id: str = Field(default_factory=lambda: f"vuln_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    severity: SeverityLevel
    cvss_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cve_id: Optional[str] = None
    target: str
    port: Optional[int] = None
    service: Optional[str] = None
    url: Optional[str] = None
    evidence: str  # Raw output showing the vulnerability
    remediation: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    discovered_by: str  # Tool that discovered it
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    exploitable: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "title": "SQL Injection in login form",
                "description": "The login parameter is vulnerable to SQL injection",
                "severity": "high",
                "cvss_score": 8.5,
                "target": "example.com",
                "port": 443,
                "url": "https://example.com/login",
                "evidence": "sqlmap identified vulnerability...",
                "remediation": "Use parameterized queries",
                "discovered_by": "sqlmap"
            }
        }


class Finding(BaseModel):
    """General security finding (not necessarily a vulnerability)"""
    finding_id: str = Field(default_factory=lambda: f"find_{uuid.uuid4().hex[:8]}")
    category: str  # e.g., "open_port", "technology_detected", "misconfiguration"
    title: str
    description: str
    target: str
    data: Dict[str, Any] = Field(default_factory=dict)
    discovered_by: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class TargetInfo(BaseModel):
    """Information about the target system"""
    target: str
    ip_addresses: List[str] = Field(default_factory=list)
    open_ports: List[int] = Field(default_factory=list)
    services: Dict[int, str] = Field(default_factory=dict)  # port -> service
    technologies: List[str] = Field(default_factory=list)
    operating_system: Optional[str] = None
    web_server: Optional[str] = None
    cms: Optional[str] = None


class ConversationMessage(BaseModel):
    """Message in the conversation history with LLM modules"""
    role: str  # "user", "assistant", "system"
    content: str
    module: Optional[str] = None  # "reasoning", "generation", "parsing"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """
    Penetration test session
    Maintains complete state and context across the testing workflow
    """
    session_id: str = Field(default_factory=lambda: f"ptest_{uuid.uuid4().hex[:12]}")
    target: str
    scope: List[str] = Field(default_factory=list)  # e.g., ["network", "web", "api"]

    # Status
    current_phase: PentestPhase = PentestPhase.RECONNAISSANCE
    status: str = "active"  # active, paused, completed, failed
    progress: float = Field(default=0.0, ge=0.0, le=100.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Target information
    target_info: TargetInfo = None
    authorized: bool = False

    # Task management
    todo_list: List[Task] = Field(default_factory=list)
    completed_tasks: List[Task] = Field(default_factory=list)
    failed_tasks: List[Task] = Field(default_factory=list)

    # Findings
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)

    # LLM context
    conversation_history: List[ConversationMessage] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        if self.target_info is None:
            self.target_info = TargetInfo(target=self.target)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    # Task Management Methods

    def add_task(self, task: Task) -> None:
        """Add a new task to the todo list"""
        self.todo_list.append(task)
        self._update_progress()

    def add_tasks(self, tasks: List[Task]) -> None:
        """Add multiple tasks to the todo list"""
        self.todo_list.extend(tasks)
        self._update_progress()

    def get_next_task(self) -> Optional[Task]:
        """Get the next pending task with highest priority"""
        pending_tasks = [t for t in self.todo_list if t.status == TaskStatus.PENDING]
        if not pending_tasks:
            return None
        return min(pending_tasks, key=lambda t: t.priority)

    def complete_task(self, task_id: str, output: str, findings_count: int = 0) -> None:
        """Mark a task as completed"""
        for task in self.todo_list:
            if task.task_id == task_id:
                task.complete(output, findings_count)
                self.completed_tasks.append(task)
                self.todo_list.remove(task)
                self._update_progress()
                break

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed"""
        for task in self.todo_list:
            if task.task_id == task_id:
                task.fail(error)
                self.failed_tasks.append(task)
                self.todo_list.remove(task)
                self._update_progress()
                break

    # Finding Management Methods

    def add_vulnerability(self, vuln: Vulnerability) -> None:
        """Add a discovered vulnerability"""
        self.vulnerabilities.append(vuln)

    def add_finding(self, finding: Finding) -> None:
        """Add a general security finding"""
        self.findings.append(finding)

    def get_vulnerabilities_by_severity(self, severity: SeverityLevel) -> List[Vulnerability]:
        """Get vulnerabilities filtered by severity"""
        return [v for v in self.vulnerabilities if v.severity == severity]

    def get_critical_vulnerabilities(self) -> List[Vulnerability]:
        """Get all critical vulnerabilities"""
        return self.get_vulnerabilities_by_severity(SeverityLevel.CRITICAL)

    # Conversation History Methods

    def add_conversation_message(self, role: str, content: str, module: Optional[str] = None) -> None:
        """Add a message to conversation history"""
        msg = ConversationMessage(role=role, content=content, module=module)
        self.conversation_history.append(msg)

    def get_conversation_summary(self, max_messages: int = 10) -> str:
        """Get recent conversation history as formatted string"""
        recent = self.conversation_history[-max_messages:]
        lines = []
        for msg in recent:
            module_prefix = f"[{msg.module}] " if msg.module else ""
            lines.append(f"{msg.role.upper()}: {module_prefix}{msg.content[:200]}")
        return "\n".join(lines)

    # Phase Management Methods

    def advance_phase(self) -> bool:
        """Advance to the next pentesting phase"""
        phase_order = [
            PentestPhase.RECONNAISSANCE,
            PentestPhase.ENUMERATION,
            PentestPhase.VULNERABILITY_SCANNING,
            PentestPhase.EXPLOITATION,
            PentestPhase.POST_EXPLOITATION,
            PentestPhase.REPORTING,
            PentestPhase.COMPLETED
        ]

        try:
            current_idx = phase_order.index(self.current_phase)
            if current_idx < len(phase_order) - 1:
                self.current_phase = phase_order[current_idx + 1]
                return True
        except ValueError:
            pass

        return False

    def can_advance_phase(self) -> bool:
        """Check if ready to advance to next phase"""
        # Must have no pending tasks in current phase
        current_phase_tasks = [
            t for t in self.todo_list
            if t.phase == self.current_phase and t.status == TaskStatus.PENDING
        ]
        return len(current_phase_tasks) == 0

    # Context Generation for LLM

    def get_context_summary(self) -> str:
        """
        Generate comprehensive context summary for LLM modules
        This is critical for maintaining awareness across interactions
        """
        lines = [
            "=== PENETRATION TEST SESSION CONTEXT ===",
            f"Session ID: {self.session_id}",
            f"Target: {self.target}",
            f"Scope: {', '.join(self.scope)}",
            f"Current Phase: {self.current_phase.value}",
            f"Progress: {self.progress:.1f}%",
            f"Status: {self.status}",
            "",
            "=== TARGET INFORMATION ===",
            f"IP Addresses: {', '.join(self.target_info.ip_addresses) or 'Not discovered yet'}",
            f"Open Ports: {', '.join(map(str, self.target_info.open_ports)) or 'Not scanned yet'}",
            f"Services: {len(self.target_info.services)} identified",
            f"Technologies: {', '.join(self.target_info.technologies) or 'None identified'}",
            "",
            "=== TASK STATUS ===",
            f"Pending Tasks: {len(self.todo_list)}",
            f"Completed Tasks: {len(self.completed_tasks)}",
            f"Failed Tasks: {len(self.failed_tasks)}",
            "",
            "=== FINDINGS ===",
            f"Total Vulnerabilities: {len(self.vulnerabilities)}",
            f"  - Critical: {len(self.get_vulnerabilities_by_severity(SeverityLevel.CRITICAL))}",
            f"  - High: {len(self.get_vulnerabilities_by_severity(SeverityLevel.HIGH))}",
            f"  - Medium: {len(self.get_vulnerabilities_by_severity(SeverityLevel.MEDIUM))}",
            f"  - Low: {len(self.get_vulnerabilities_by_severity(SeverityLevel.LOW))}",
            f"General Findings: {len(self.findings)}",
            "",
            "=== RECENT COMPLETED TASKS ===",
        ]

        # Add recent completed tasks
        for task in self.completed_tasks[-5:]:
            lines.append(f"- [{task.tool or 'manual'}] {task.description} ({task.findings_count} findings)")

        # Add current todo list
        lines.append("")
        lines.append("=== TODO LIST (Next Tasks) ===")
        for task in self.todo_list[:10]:  # Show max 10 tasks
            status_icon = "▶" if task.status == TaskStatus.IN_PROGRESS else "⏸"
            lines.append(f"{status_icon} [P{task.priority}] {task.description}")

        return "\n".join(lines)

    def get_vulnerabilities_summary(self) -> str:
        """Get formatted summary of discovered vulnerabilities"""
        if not self.vulnerabilities:
            return "No vulnerabilities discovered yet."

        lines = ["=== DISCOVERED VULNERABILITIES ==="]
        for vuln in sorted(self.vulnerabilities, key=lambda v: v.severity.value):
            lines.append(f"\n[{vuln.severity.value.upper()}] {vuln.title}")
            lines.append(f"  Target: {vuln.target}")
            if vuln.port:
                lines.append(f"  Port: {vuln.port}")
            lines.append(f"  Tool: {vuln.discovered_by}")
            lines.append(f"  Description: {vuln.description[:150]}...")

        return "\n".join(lines)

    # Progress Tracking

    def _update_progress(self) -> None:
        """Update overall progress percentage"""
        total_tasks = len(self.todo_list) + len(self.completed_tasks) + len(self.failed_tasks)
        if total_tasks == 0:
            self.progress = 0.0
        else:
            self.progress = (len(self.completed_tasks) / total_tasks) * 100.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "target": self.target,
            "phase": self.current_phase.value,
            "progress": self.progress,
            "duration_minutes": self.get_duration_minutes(),
            "tasks": {
                "total": len(self.todo_list) + len(self.completed_tasks) + len(self.failed_tasks),
                "pending": len(self.todo_list),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks)
            },
            "findings": {
                "vulnerabilities": len(self.vulnerabilities),
                "critical": len(self.get_vulnerabilities_by_severity(SeverityLevel.CRITICAL)),
                "high": len(self.get_vulnerabilities_by_severity(SeverityLevel.HIGH)),
                "medium": len(self.get_vulnerabilities_by_severity(SeverityLevel.MEDIUM)),
                "low": len(self.get_vulnerabilities_by_severity(SeverityLevel.LOW)),
                "informational": len(self.get_vulnerabilities_by_severity(SeverityLevel.INFORMATIONAL)),
                "general_findings": len(self.findings)
            }
        }

    def get_duration_minutes(self) -> Optional[float]:
        """Get session duration in minutes"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds() / 60.0
        return round(duration, 2)

    # Persistence Methods

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return self.model_dump(mode='json')

    def save(self, directory: Optional[Path] = None) -> Path:
        """Save session to JSON file"""
        if directory is None:
            from .config import config
            directory = Path(config.settings.sessions_dir)

        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{self.session_id}.json"

        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        return file_path

    @classmethod
    def load(cls, session_id: str, directory: Optional[Path] = None) -> 'Session':
        """Load session from JSON file"""
        if directory is None:
            from .config import config
            directory = Path(config.settings.sessions_dir)

        file_path = directory / f"{session_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        with open(file_path, 'r') as f:
            data = json.load(f)

        return cls(**data)

    @classmethod
    def list_sessions(cls, directory: Optional[Path] = None) -> List[str]:
        """List all saved session IDs"""
        if directory is None:
            from .config import config
            directory = Path(config.settings.sessions_dir)

        if not directory.exists():
            return []

        return [f.stem for f in directory.glob("ptest_*.json")]
