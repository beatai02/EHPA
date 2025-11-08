"""
Hexstrike MCP Wrapper
Unified interface to 150+ security tools via Hexstrike MCP Server
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class HexstrikeMCPClient:
    """
    Client for Hexstrike MCP Server
    Provides unified access to 150+ security tools
    """

    def __init__(
        self,
        mcp_url: str = "http://localhost:8888",
        api_key: Optional[str] = None,
        timeout: int = 300
    ):
        """
        Initialize Hexstrike MCP client

        Args:
            mcp_url: Base URL of Hexstrike MCP server
            api_key: API key for authentication
            timeout: Default timeout for tool execution (seconds)
        """
        self.mcp_url = mcp_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.available_tools: List[str] = []

    async def connect(self) -> bool:
        """
        Connect to Hexstrike MCP server and verify availability

        Returns:
            bool: True if connection successful
        """
        try:
            self.session = aiohttp.ClientSession()

            # Test health endpoint
            async with self.session.get(
                f"{self.mcp_url}/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.connected = True
                    logger.info("✅ Connected to Hexstrike MCP server")

                    # Fetch available tools
                    await self.refresh_tools()
                    return True
                else:
                    logger.error(f"❌ Hexstrike MCP health check failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Hexstrike MCP: {e}")
            self.connected = False
            return False

    async def refresh_tools(self) -> List[str]:
        """
        Fetch list of available tools from Hexstrike MCP

        Returns:
            List of tool names
        """
        try:
            async with self.session.get(
                f"{self.mcp_url}/tools",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_tools = data.get("tools", [])
                    logger.info(f"📋 {len(self.available_tools)} tools available from Hexstrike")
                    return self.available_tools
                else:
                    logger.error(f"Failed to fetch tools: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching tools: {e}")
            return []

    async def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific tool

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information dictionary
        """
        try:
            async with self.session.get(
                f"{self.mcp_url}/tools/{tool_name}",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Tool {tool_name} not found")
                    return None

        except Exception as e:
            logger.error(f"Error fetching tool info: {e}")
            return None

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Execute a security tool via Hexstrike MCP

        Args:
            tool_name: Name of the tool to execute
            params: Tool-specific parameters
            timeout: Execution timeout (uses default if None)

        Returns:
            Execution result dictionary with:
                - tool: Tool name
                - status: success/failed/timeout
                - output: Raw tool output
                - parsed: Parsed results (if available)
                - error: Error message (if failed)
                - duration: Execution time in seconds
                - timestamp: Execution timestamp
        """
        start_time = datetime.utcnow()

        # Validate connection
        if not self.connected:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": "Not connected to Hexstrike MCP server",
                "output": None,
                "duration": 0,
                "timestamp": start_time.isoformat()
            }

        # Check tool availability
        if tool_name not in self.available_tools:
            logger.warning(f"Tool '{tool_name}' not in available tools list")

        try:
            payload = {
                "tool": tool_name,
                "params": params,
                "timeout": timeout or self.timeout
            }

            logger.info(f"🔧 Executing {tool_name} via Hexstrike MCP")

            async with self.session.post(
                f"{self.mcp_url}/execute",
                json=payload,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=(timeout or self.timeout) + 30)
            ) as response:

                result = await response.json()
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                if response.status == 200:
                    return {
                        "tool": tool_name,
                        "status": result.get("status", "success"),
                        "output": result.get("output", ""),
                        "parsed": result.get("parsed", {}),
                        "error": result.get("error"),
                        "duration": result.get("duration", duration),
                        "timestamp": start_time.isoformat()
                    }
                else:
                    return {
                        "tool": tool_name,
                        "status": "failed",
                        "error": result.get("error", f"HTTP {response.status}"),
                        "output": result.get("output"),
                        "duration": duration,
                        "timestamp": start_time.isoformat()
                    }

        except asyncio.TimeoutError:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"⏱️ Tool execution timeout: {tool_name}")
            return {
                "tool": tool_name,
                "status": "timeout",
                "error": f"Execution timeout after {timeout or self.timeout}s",
                "output": None,
                "duration": duration,
                "timestamp": start_time.isoformat()
            }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Tool execution error ({tool_name}): {e}")
            return {
                "tool": tool_name,
                "status": "failed",
                "error": str(e),
                "output": None,
                "duration": duration,
                "timestamp": start_time.isoformat()
            }

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Execute multiple tools in parallel

        Args:
            tasks: List of task dictionaries with 'tool' and 'params'

        Returns:
            List of execution results
        """
        logger.info(f"🔄 Executing batch of {len(tasks)} tools")

        coroutines = [
            self.execute_tool(
                task["tool"],
                task.get("params", {}),
                task.get("timeout")
            )
            for task in tasks
        ]

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "tool": tasks[i]["tool"],
                    "status": "failed",
                    "error": str(result),
                    "output": None,
                    "duration": 0,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)

        return processed_results

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get parameter schema for a tool

        Args:
            tool_name: Name of the tool

        Returns:
            JSON schema describing tool parameters
        """
        try:
            async with self.session.get(
                f"{self.mcp_url}/tools/{tool_name}/schema",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Error fetching tool schema: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including authentication"""
        headers = {
            "Content-Type": "application/json"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.connected = False
            logger.info("Closed Hexstrike MCP connection")

    def is_connected(self) -> bool:
        """Check if connected to Hexstrike MCP"""
        return self.connected

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return self.available_tools.copy()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Tool category mappings for organization
HEXSTRIKE_TOOL_CATEGORIES = {
    "network_scanning": [
        "nmap", "masscan", "rustscan", "zmap"
    ],
    "web_scanning": [
        "nikto", "whatweb", "wpscan", "nuclei"
    ],
    "directory_enumeration": [
        "gobuster", "dirb", "dirbuster", "ffuf", "feroxbuster"
    ],
    "service_enumeration": [
        "enum4linux", "dnsenum", "smbclient", "ldapsearch"
    ],
    "osint": [
        "theharvester", "shodan", "amass", "subfinder", "recon-ng", "maltego"
    ],
    "exploitation": [
        "metasploit", "sqlmap", "searchsploit", "exploitdb"
    ],
    "password_cracking": [
        "hashcat", "john", "hydra", "medusa"
    ],
    "wireless": [
        "aircrack-ng", "wifite", "reaver", "bully"
    ],
    "forensics": [
        "volatility", "autopsy", "sleuthkit"
    ],
    "web_exploitation": [
        "burpsuite", "owasp-zap", "sqlmap", "xsser", "commix"
    ],
    "privilege_escalation": [
        "linpeas", "winpeas", "linux-exploit-suggester", "windows-exploit-suggester"
    ],
    "post_exploitation": [
        "mimikatz", "bloodhound", "powersploit", "empire"
    ]
}


def get_tools_by_category(category: str) -> List[str]:
    """Get list of tools in a category"""
    return HEXSTRIKE_TOOL_CATEGORIES.get(category, [])


def get_tool_category(tool_name: str) -> Optional[str]:
    """Get category for a tool"""
    for category, tools in HEXSTRIKE_TOOL_CATEGORIES.items():
        if tool_name.lower() in tools:
            return category
    return None


# Example usage
async def example_usage():
    """Example usage of Hexstrike MCP client"""

    # Initialize client
    client = HexstrikeMCPClient(
        mcp_url="http://localhost:8888",
        api_key="your-api-key-here"
    )

    try:
        # Connect to server
        if await client.connect():

            # Get available tools
            tools = client.get_available_tools()
            print(f"Available tools: {len(tools)}")

            # Execute single tool
            result = await client.execute_tool(
                "nmap",
                {
                    "target": "192.168.1.1",
                    "ports": "1-1000",
                    "scan_type": "syn"
                }
            )
            print(f"Nmap result: {result['status']}")

            # Execute multiple tools in parallel
            tasks = [
                {"tool": "nmap", "params": {"target": "192.168.1.1"}},
                {"tool": "whatweb", "params": {"url": "http://example.com"}},
                {"tool": "nikto", "params": {"target": "http://example.com"}}
            ]
            results = await client.execute_batch(tasks)
            print(f"Executed {len(results)} tools")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
