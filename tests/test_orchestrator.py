"""
Tests for Core Orchestrator
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.core.orchestrator import Orchestrator
from src.core.session import Session, PentestPhase, Task, Vulnerability, SeverityLevel


@pytest.fixture
async def orchestrator():
    """Create orchestrator instance for testing"""
    with patch('src.core.orchestrator.config') as mock_config:
        mock_config.settings.anthropic_api_key = "test-key"
        mock_config.llm.model = "claude-sonnet-4-5-20250929"
        mock_config.security.require_target_approval = False

        orch = Orchestrator()
        yield orch

        # Cleanup
        await orch.cleanup()


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes correctly"""
    assert orchestrator.reasoning is not None
    assert orchestrator.generation is not None
    assert orchestrator.parsing is not None
    assert orchestrator.tools is not None
    assert len(orchestrator.tools) >= 4
    assert orchestrator.chatbot_manager is not None


@pytest.mark.asyncio
async def test_start_pentest_creates_session(orchestrator):
    """Test starting a new pentest creates a session"""
    target = "scanme.nmap.org"
    scope = ["network", "web"]

    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target=target,
            scope=scope,
            authorized=True
        )

    assert session is not None
    assert session.target == target
    assert session.scope == scope
    assert session.authorized == True
    assert session.status == "active"
    assert session.current_phase == PentestPhase.RECONNAISSANCE
    assert session.session_id in orchestrator.sessions


@pytest.mark.asyncio
async def test_start_pentest_unauthorized_target_fails(orchestrator):
    """Test unauthorized target is rejected"""
    with patch('src.core.orchestrator.config') as mock_config:
        mock_config.security.require_target_approval = True
        mock_config.is_target_allowed.return_value = False

        with pytest.raises(ValueError, match="not in the approved list"):
            await orchestrator.start_pentest(
                target="unauthorized.com",
                scope=["network"],
                authorized=False
            )


@pytest.mark.asyncio
async def test_get_session_retrieves_session(orchestrator):
    """Test getting an existing session"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="test.com",
            scope=["network"],
            authorized=True
        )

    retrieved = orchestrator.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id


@pytest.mark.asyncio
async def test_list_sessions_returns_all_sessions(orchestrator):
    """Test listing all sessions"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        await orchestrator.start_pentest(
            target="test1.com",
            scope=["network"],
            authorized=True
        )
        await orchestrator.start_pentest(
            target="test2.com",
            scope=["web"],
            authorized=True
        )

    sessions = orchestrator.list_sessions()
    assert len(sessions) >= 2
    assert all('session_id' in s for s in sessions)
    assert all('target' in s for s in sessions)


@pytest.mark.asyncio
async def test_execute_task_runs_tool(orchestrator):
    """Test executing a single task"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="scanme.nmap.org",
            scope=["network"],
            authorized=True
        )

    # Add a task
    task = Task(
        description="Test nmap scan",
        tool="nmap",
        phase=PentestPhase.RECONNAISSANCE,
        priority=1
    )
    session.add_task(task)

    # Mock tool execution
    with patch.object(orchestrator.tools['nmap'], 'execute',
                     return_value={'output': 'test output', 'status': 'success'}):
        with patch.object(orchestrator.generation, 'generate_command',
                         return_value={'command': 'nmap -sV test.com'}):
            with patch.object(orchestrator.parsing, 'parse_tool_output',
                             return_value={'vulnerabilities': [], 'findings': []}):
                await orchestrator._execute_task(session, task)

    assert task.status.value == "completed"


@pytest.mark.asyncio
async def test_pause_and_resume_session(orchestrator):
    """Test pausing and resuming a session"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="test.com",
            scope=["network"],
            authorized=True
        )

    # Pause
    await orchestrator.pause_session(session.session_id)
    assert session.status == "paused"

    # Resume
    with patch.object(orchestrator, 'execute_workflow'):
        await orchestrator.resume_session(session.session_id)
        assert session.status == "active"


@pytest.mark.asyncio
async def test_generate_report(orchestrator):
    """Test report generation"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="test.com",
            scope=["network"],
            authorized=True
        )

    # Add some test vulnerabilities
    session.add_vulnerability(Vulnerability(
        title="Test Vulnerability",
        description="Test description",
        severity=SeverityLevel.HIGH,
        target="test.com",
        evidence="Test evidence",
        discovered_by="nmap"
    ))

    with patch('src.core.orchestrator.generate_report',
              return_value="/tmp/test_report.html"):
        report_path = await orchestrator.generate_report(session.session_id)
        assert report_path is not None


@pytest.mark.asyncio
async def test_workflow_execution_advances_phases(orchestrator):
    """Test that workflow execution advances through phases"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="test.com",
            scope=["network"],
            authorized=True
        )

    # Mock all the necessary methods
    with patch.object(orchestrator.reasoning, 'should_escalate_phase',
                     return_value=True):
        with patch.object(orchestrator.reasoning, 'plan_next_steps',
                         return_value=[]):
            with patch.object(orchestrator.reasoning, 'analyze_findings',
                             return_value={"summary": "test"}):
                with patch('src.core.orchestrator.generate_report',
                          return_value="/tmp/report.html"):
                    # Run workflow with max_iterations=5 to prevent infinite loop
                    await orchestrator.execute_workflow(session.session_id, max_iterations=5)

    # Session should have progressed
    assert session.current_phase in [
        PentestPhase.ENUMERATION,
        PentestPhase.VULNERABILITY_SCANNING,
        PentestPhase.REPORTING,
        PentestPhase.COMPLETED
    ]


@pytest.mark.asyncio
async def test_cleanup_saves_sessions(orchestrator):
    """Test cleanup saves all active sessions"""
    with patch.object(orchestrator.reasoning, 'plan_initial_tasks',
                     return_value=[]):
        session = await orchestrator.start_pentest(
            target="test.com",
            scope=["network"],
            authorized=True
        )

    with patch.object(session, 'save') as mock_save:
        await orchestrator.cleanup()
        mock_save.assert_called()


def test_orchestrator_has_all_required_tools(orchestrator):
    """Test orchestrator has all required tools"""
    required_tools = ['nmap', 'nikto', 'sqlmap', 'gobuster']

    for tool in required_tools:
        assert tool in orchestrator.tools


def test_orchestrator_has_all_agents(orchestrator):
    """Test orchestrator has all phase agents"""
    assert orchestrator.recon_agent is not None
    assert orchestrator.enum_agent is not None
    assert orchestrator.vuln_agent is not None
    assert orchestrator.exploit_agent is not None
    assert orchestrator.report_agent is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
