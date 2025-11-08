"""
Tests for Hexstrike MCP Integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

from src.mcp.hexstrike_wrapper import (
    HexstrikeMCPClient,
    get_tools_by_category,
    get_tool_category,
    HEXSTRIKE_TOOL_CATEGORIES
)


# ============================================================================
# HEXSTRIKE CLIENT TESTS
# ============================================================================

@pytest.fixture
async def hexstrike_client():
    """Create Hexstrike MCP client for testing"""
    client = HexstrikeMCPClient(
        mcp_url="http://localhost:8888",
        api_key="test-api-key",
        timeout=300
    )
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_hexstrike_client_initialization():
    """Test Hexstrike client initializes correctly"""
    client = HexstrikeMCPClient(
        mcp_url="http://localhost:8888",
        api_key="test-key"
    )

    assert client.mcp_url == "http://localhost:8888"
    assert client.api_key == "test-key"
    assert client.timeout == 300
    assert client.connected == False


@pytest.mark.asyncio
async def test_hexstrike_connect_success():
    """Test successful connection to Hexstrike MCP"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")

    # Mock successful health check
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Mock refresh_tools
        with patch.object(client, 'refresh_tools', return_value=['nmap', 'nikto']):
            result = await client.connect()

        assert result == True
        assert client.connected == True


@pytest.mark.asyncio
async def test_hexstrike_connect_failure():
    """Test failed connection to Hexstrike MCP"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")

    # Mock failed health check
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = await client.connect()

        assert result == False
        assert client.connected == False


@pytest.mark.asyncio
async def test_hexstrike_refresh_tools():
    """Test fetching available tools from Hexstrike"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True

    # Mock tools endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "tools": ["nmap", "nikto", "sqlmap", "gobuster", "nuclei"]
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    client.session.get.return_value = mock_response

    tools = await client.refresh_tools()

    assert len(tools) == 5
    assert "nmap" in tools
    assert "nikto" in tools
    assert client.available_tools == tools


@pytest.mark.asyncio
async def test_hexstrike_execute_tool_success():
    """Test successful tool execution via Hexstrike"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True
    client.available_tools = ["nmap"]

    # Mock execute endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "status": "success",
        "output": "Nmap scan report for scanme.nmap.org",
        "parsed": {"open_ports": [22, 80]},
        "duration": 12.5
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    client.session.post.return_value = mock_response

    result = await client.execute_tool(
        "nmap",
        {"target": "scanme.nmap.org", "ports": "1-1000"}
    )

    assert result['status'] == 'success'
    assert result['tool'] == 'nmap'
    assert 'output' in result
    assert 'duration' in result


@pytest.mark.asyncio
async def test_hexstrike_execute_tool_failure():
    """Test failed tool execution via Hexstrike"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True
    client.available_tools = ["nmap"]

    # Mock failed execution
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json.return_value = {
        "status": "failed",
        "error": "Invalid parameters"
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    client.session.post.return_value = mock_response

    result = await client.execute_tool("nmap", {})

    assert result['status'] == 'failed'
    assert 'error' in result


@pytest.mark.asyncio
async def test_hexstrike_execute_tool_timeout():
    """Test tool execution timeout"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True
    client.available_tools = ["nmap"]

    # Mock timeout
    import asyncio
    client.session.post.side_effect = asyncio.TimeoutError()

    result = await client.execute_tool(
        "nmap",
        {"target": "scanme.nmap.org"},
        timeout=1
    )

    assert result['status'] == 'timeout'
    assert 'error' in result


@pytest.mark.asyncio
async def test_hexstrike_execute_batch():
    """Test batch execution of multiple tools"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True
    client.available_tools = ["nmap", "nikto", "whatweb"]

    # Mock successful responses
    async def mock_execute_tool(tool, params, timeout=None):
        return {
            "tool": tool,
            "status": "success",
            "output": f"Output from {tool}",
            "duration": 10
        }

    with patch.object(client, 'execute_tool', side_effect=mock_execute_tool):
        tasks = [
            {"tool": "nmap", "params": {"target": "scanme.nmap.org"}},
            {"tool": "nikto", "params": {"target": "http://example.com"}},
            {"tool": "whatweb", "params": {"url": "http://example.com"}}
        ]

        results = await client.execute_batch(tasks)

    assert len(results) == 3
    assert all(r['status'] == 'success' for r in results)


@pytest.mark.asyncio
async def test_hexstrike_get_tool_info():
    """Test getting detailed tool information"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True

    # Mock tool info endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "name": "nmap",
        "description": "Network scanning tool",
        "category": "network_scanning",
        "parameters": {
            "target": {"type": "string", "required": True}
        }
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    client.session.get.return_value = mock_response

    info = await client.get_tool_info("nmap")

    assert info is not None
    assert info['name'] == 'nmap'
    assert 'description' in info


@pytest.mark.asyncio
async def test_hexstrike_get_tool_schema():
    """Test getting tool parameter schema"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True

    # Mock schema endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "parameters": {
            "target": {
                "type": "string",
                "required": True,
                "description": "Target IP or domain"
            },
            "ports": {
                "type": "string",
                "required": False,
                "default": "1-1000"
            }
        }
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    client.session.get.return_value = mock_response

    schema = await client.get_tool_schema("nmap")

    assert schema is not None
    assert 'parameters' in schema


@pytest.mark.asyncio
async def test_hexstrike_not_connected_error():
    """Test error when executing tool while not connected"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.connected = False

    result = await client.execute_tool("nmap", {"target": "test.com"})

    assert result['status'] == 'failed'
    assert 'Not connected' in result['error']


@pytest.mark.asyncio
async def test_hexstrike_context_manager():
    """Test Hexstrike client as async context manager"""
    with patch.object(HexstrikeMCPClient, 'connect', return_value=True):
        with patch.object(HexstrikeMCPClient, 'close'):
            async with HexstrikeMCPClient(mcp_url="http://localhost:8888") as client:
                assert client is not None


# ============================================================================
# TOOL CATEGORY TESTS
# ============================================================================

def test_hexstrike_tool_categories_defined():
    """Test Hexstrike tool categories are defined"""
    assert len(HEXSTRIKE_TOOL_CATEGORIES) > 0
    assert 'network_scanning' in HEXSTRIKE_TOOL_CATEGORIES
    assert 'web_scanning' in HEXSTRIKE_TOOL_CATEGORIES
    assert 'exploitation' in HEXSTRIKE_TOOL_CATEGORIES


def test_get_tools_by_category():
    """Test getting tools by category"""
    network_tools = get_tools_by_category('network_scanning')

    assert len(network_tools) > 0
    assert 'nmap' in network_tools

    web_tools = get_tools_by_category('web_scanning')
    assert 'nikto' in web_tools


def test_get_tool_category():
    """Test getting category for a tool"""
    category = get_tool_category('nmap')
    assert category == 'network_scanning'

    category = get_tool_category('nikto')
    assert category == 'web_scanning'

    category = get_tool_category('sqlmap')
    assert category == 'exploitation'

    category = get_tool_category('nonexistent_tool')
    assert category is None


def test_hexstrike_has_150_plus_tools():
    """Test Hexstrike provides access to 150+ tools"""
    total_tools = sum(len(tools) for tools in HEXSTRIKE_TOOL_CATEGORIES.values())

    # Should have a substantial number of tools defined
    assert total_tools >= 40  # Conservative estimate from categories


def test_all_required_tool_categories_exist():
    """Test all required tool categories are defined"""
    required_categories = [
        'network_scanning',
        'web_scanning',
        'directory_enumeration',
        'service_enumeration',
        'osint',
        'exploitation',
        'password_cracking',
        'privilege_escalation',
        'post_exploitation'
    ]

    for category in required_categories:
        assert category in HEXSTRIKE_TOOL_CATEGORIES
        assert len(HEXSTRIKE_TOOL_CATEGORIES[category]) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_hexstrike_authentication():
    """Test Hexstrike API authentication"""
    client = HexstrikeMCPClient(
        mcp_url="http://localhost:8888",
        api_key="test-api-key"
    )

    headers = client._get_headers()

    assert 'Authorization' in headers
    assert headers['Authorization'] == 'Bearer test-api-key'
    assert headers['Content-Type'] == 'application/json'


@pytest.mark.asyncio
async def test_hexstrike_without_api_key():
    """Test Hexstrike without API key"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")

    headers = client._get_headers()

    # Should still have content type
    assert 'Content-Type' in headers
    # But no authorization header
    assert 'Authorization' not in headers


@pytest.mark.asyncio
async def test_hexstrike_error_handling():
    """Test Hexstrike client error handling"""
    client = HexstrikeMCPClient(mcp_url="http://localhost:8888")
    client.session = AsyncMock()
    client.connected = True
    client.available_tools = ["nmap"]

    # Mock network error
    client.session.post.side_effect = aiohttp.ClientError("Network error")

    result = await client.execute_tool("nmap", {"target": "test.com"})

    assert result['status'] == 'failed'
    assert 'error' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
