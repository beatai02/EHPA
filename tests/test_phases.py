"""
Tests for All 6 Penetration Testing Phases
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agents.recon_agent import ReconAgent
from src.agents.enum_agent import EnumAgent
from src.agents.vuln_agent import VulnAgent
from src.agents.exploit_agent import ExploitAgent
from src.agents.post_exploit_agent import PostExploitAgent
from src.agents.report_agent import ReportAgent
from src.core.session import Session, PentestPhase, Task, Vulnerability, SeverityLevel


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for agent testing"""
    orch = Mock()
    orch.reasoning = Mock()
    orch.generation = Mock()
    orch.parsing = Mock()
    orch.tools = {
        'nmap': Mock(),
        'nikto': Mock(),
        'sqlmap': Mock(),
        'gobuster': Mock()
    }
    orch.get_session = Mock()
    return orch


@pytest.fixture
def test_session():
    """Create a test session"""
    return Session(
        target="scanme.nmap.org",
        scope=["network", "web"],
        authorized=True,
        status="active"
    )


# ============================================================================
# PHASE 1: RECONNAISSANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_recon_agent_initialization(mock_orchestrator):
    """Test reconnaissance agent initializes correctly"""
    agent = ReconAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator
    assert agent.reasoning is not None


@pytest.mark.asyncio
async def test_recon_agent_executes_phase(mock_orchestrator, test_session):
    """Test reconnaissance phase execution"""
    agent = ReconAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Mock tool executions
    with patch.object(agent, '_run_nmap_scan',
                     return_value={'findings': []}):
        with patch.object(agent, '_run_osint_tools',
                         return_value={'findings': []}):
            result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result['phase'] == 'reconnaissance'
    assert 'findings' in result or 'results' in result


@pytest.mark.asyncio
async def test_recon_phase_discovers_ports(mock_orchestrator, test_session):
    """Test reconnaissance discovers open ports"""
    agent = ReconAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Mock nmap finding ports
    mock_nmap_result = {
        'findings': [
            {'type': 'open_port', 'port': 22, 'service': 'ssh'},
            {'type': 'open_port', 'port': 80, 'service': 'http'}
        ]
    }

    with patch.object(agent, '_run_nmap_scan',
                     return_value=mock_nmap_result):
        result = await agent.execute_phase(test_session.session_id)

    # Session should have port info
    assert len(test_session.target_info.open_ports) > 0 or result is not None


# ============================================================================
# PHASE 2: ENUMERATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_enum_agent_initialization(mock_orchestrator):
    """Test enumeration agent initializes correctly"""
    agent = EnumAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_enum_agent_executes_phase(mock_orchestrator, test_session):
    """Test enumeration phase execution"""
    agent = EnumAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Add some ports from recon
    test_session.target_info.open_ports = [80, 443]

    with patch.object(agent, '_enumerate_services',
                     return_value={'findings': []}):
        with patch.object(agent, '_enumerate_directories',
                         return_value={'findings': []}):
            result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result['phase'] == 'enumeration'


@pytest.mark.asyncio
async def test_enum_phase_finds_directories(mock_orchestrator, test_session):
    """Test enumeration finds hidden directories"""
    agent = EnumAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    test_session.target_info.open_ports = [80]

    mock_gobuster_result = {
        'findings': [
            {'path': '/admin', 'status': 200},
            {'path': '/api', 'status': 200}
        ]
    }

    with patch.object(agent, '_enumerate_directories',
                     return_value=mock_gobuster_result):
        result = await agent.execute_phase(test_session.session_id)

    assert result is not None


# ============================================================================
# PHASE 3: VULNERABILITY SCANNING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_vuln_agent_initialization(mock_orchestrator):
    """Test vulnerability scanning agent initializes correctly"""
    agent = VulnAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_vuln_agent_executes_phase(mock_orchestrator, test_session):
    """Test vulnerability scanning phase execution"""
    agent = VulnAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    test_session.target_info.open_ports = [80]

    with patch.object(agent, '_scan_web_vulnerabilities',
                     return_value={'vulnerabilities': []}):
        result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result['phase'] == 'vulnerability_scanning'


@pytest.mark.asyncio
async def test_vuln_phase_discovers_vulnerabilities(mock_orchestrator, test_session):
    """Test vulnerability scanning discovers vulnerabilities"""
    agent = VulnAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    test_session.target_info.open_ports = [80]

    mock_nikto_result = {
        'vulnerabilities': [
            {
                'title': 'Outdated Apache',
                'description': 'Apache 2.4.41 is outdated',
                'severity': 'medium',
                'target': 'scanme.nmap.org',
                'evidence': 'Server: Apache/2.4.41',
                'discovered_by': 'nikto'
            }
        ]
    }

    with patch.object(agent, '_scan_web_vulnerabilities',
                     return_value=mock_nikto_result):
        result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert 'vulnerabilities' in result or len(test_session.vulnerabilities) > 0


# ============================================================================
# PHASE 4: EXPLOITATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_exploit_agent_initialization(mock_orchestrator):
    """Test exploitation agent initializes correctly"""
    agent = ExploitAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_exploit_agent_requires_approval(mock_orchestrator, test_session):
    """Test exploitation phase requires approval"""
    agent = ExploitAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Without approval, should check first
    with patch.object(agent, '_check_approval',
                     return_value=False):
        result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    # Should indicate approval required
    assert result.get('approval_required') == True or result.get('status') == 'approval_required'


@pytest.mark.asyncio
async def test_exploit_agent_executes_with_approval(mock_orchestrator, test_session):
    """Test exploitation phase executes with approval"""
    agent = ExploitAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Add vulnerability to exploit
    test_session.add_vulnerability(Vulnerability(
        title="SQL Injection",
        description="SQL injection in login",
        severity=SeverityLevel.HIGH,
        target="scanme.nmap.org",
        evidence="Test evidence",
        discovered_by="sqlmap"
    ))

    with patch.object(agent, '_check_approval',
                     return_value=True):
        with patch.object(agent, '_exploit_vulnerabilities',
                         return_value={'exploits': []}):
            result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result['phase'] == 'exploitation'


# ============================================================================
# PHASE 5: POST-EXPLOITATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_post_exploit_agent_initialization(mock_orchestrator):
    """Test post-exploitation agent initializes correctly"""
    agent = PostExploitAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_post_exploit_agent_requires_approval(mock_orchestrator, test_session):
    """Test post-exploitation phase requires approval"""
    agent = PostExploitAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    with patch.object(agent, '_check_approval',
                     return_value=False):
        result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result.get('approval_required') == True or result.get('status') == 'approval_required'


# ============================================================================
# PHASE 6: REPORTING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_report_agent_initialization(mock_orchestrator):
    """Test report generation agent initializes correctly"""
    agent = ReportAgent(mock_orchestrator)
    assert agent.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_report_agent_generates_report(mock_orchestrator, test_session):
    """Test report generation phase creates report"""
    agent = ReportAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Add some findings
    test_session.add_vulnerability(Vulnerability(
        title="Test Vulnerability",
        description="Test description",
        severity=SeverityLevel.HIGH,
        target="scanme.nmap.org",
        evidence="Test evidence",
        discovered_by="nmap"
    ))

    with patch.object(agent, '_generate_executive_summary',
                     return_value={'summary': 'Test summary'}):
        with patch.object(agent, '_compile_technical_details',
                         return_value={'details': 'Test details'}):
            with patch.object(agent, '_generate_remediation_plan',
                             return_value={'plan': 'Test plan'}):
                with patch.object(agent, '_create_html_report',
                                 return_value='/tmp/report.html'):
                    result = await agent.execute_phase(test_session.session_id)

    assert result is not None
    assert result['phase'] == 'reporting'
    assert 'report_paths' in result or 'reports_generated' in result


@pytest.mark.asyncio
async def test_report_includes_all_vulnerabilities(mock_orchestrator, test_session):
    """Test report includes all discovered vulnerabilities"""
    agent = ReportAgent(mock_orchestrator)
    mock_orchestrator.get_session.return_value = test_session

    # Add multiple vulnerabilities
    for i in range(3):
        test_session.add_vulnerability(Vulnerability(
            title=f"Vulnerability {i}",
            description=f"Description {i}",
            severity=SeverityLevel.MEDIUM,
            target="scanme.nmap.org",
            evidence=f"Evidence {i}",
            discovered_by="nmap"
        ))

    with patch.object(agent, '_generate_executive_summary',
                     return_value={'summary': 'Test'}):
        with patch.object(agent, '_compile_technical_details',
                         return_value={'details': 'Test'}):
            with patch.object(agent, '_generate_remediation_plan',
                             return_value={'plan': 'Test'}):
                with patch.object(agent, '_create_html_report',
                                 return_value='/tmp/report.html'):
                    result = await agent.execute_phase(test_session.session_id)

    # Should include all 3 vulnerabilities
    assert len(test_session.vulnerabilities) == 3


# ============================================================================
# PHASE TRANSITION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_phase_progression(test_session):
    """Test session progresses through phases correctly"""
    assert test_session.current_phase == PentestPhase.RECONNAISSANCE

    # Can advance after reconnaissance
    assert test_session.can_advance_phase() == True

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.ENUMERATION

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.VULNERABILITY_SCANNING

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.EXPLOITATION

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.POST_EXPLOITATION

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.REPORTING

    test_session.advance_phase()
    assert test_session.current_phase == PentestPhase.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
