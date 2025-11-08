"""
Pydantic Models for API
Request and response models for REST API endpoints
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Request Models

class PentestStartRequest(BaseModel):
    """Request to start a new penetration test"""
    target: str = Field(..., description="Target domain or IP address")
    scope: List[str] = Field(default=["network", "web"], description="Testing scope")
    authorized: bool = Field(default=False, description="Whether target testing is authorized")

    class Config:
        json_schema_extra = {
            "example": {
                "target": "scanme.nmap.org",
                "scope": ["network", "web"],
                "authorized": True
            }
        }


class ExecuteTaskRequest(BaseModel):
    """Request to execute a specific task"""
    task_id: str = Field(..., description="ID of the task to execute")


# Response Models

class PentestStartResponse(BaseModel):
    """Response when starting a pentest"""
    session_id: str
    target: str
    status: str
    current_phase: str
    created_at: datetime
    message: str = "Penetration test session created successfully"


class SessionStatusResponse(BaseModel):
    """Response for session status"""
    session_id: str
    target: str
    phase: str
    status: str
    progress: float
    current_task: Optional[str] = None
    tasks_pending: int
    tasks_completed: int
    findings_count: int
    vulnerabilities_count: int
    duration_minutes: Optional[float]


class TaskInfo(BaseModel):
    """Information about a task"""
    task_id: str
    description: str
    tool: Optional[str]
    status: str
    priority: int
    findings_count: int


class FindingsResponse(BaseModel):
    """Response with discovered findings"""
    session_id: str
    total_vulnerabilities: int
    critical: int
    high: int
    medium: int
    low: int
    informational: int
    vulnerabilities: List[Dict[str, Any]]
    general_findings: int


class VulnerabilityDetail(BaseModel):
    """Detailed vulnerability information"""
    vuln_id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float]
    target: str
    port: Optional[int]
    service: Optional[str]
    url: Optional[str]
    evidence: str
    remediation: Optional[str]
    discovered_by: str
    discovered_at: datetime


class SessionListResponse(BaseModel):
    """Response with list of sessions"""
    sessions: List[Dict[str, Any]]
    total: int


class TaskExecutionResponse(BaseModel):
    """Response after task execution"""
    task_id: str
    status: str
    findings_count: int
    output_preview: Optional[str]
    message: str


class ReportResponse(BaseModel):
    """Response with report information"""
    session_id: str
    report_path: str
    report_url: Optional[str]
    generated_at: datetime
    message: str = "Report generated successfully"


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


class StatisticsResponse(BaseModel):
    """Session statistics"""
    session_id: str
    target: str
    phase: str
    progress: float
    duration_minutes: Optional[float]
    tasks: Dict[str, int]
    findings: Dict[str, int]
