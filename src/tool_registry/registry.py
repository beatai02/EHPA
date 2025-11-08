"""
Centralized Tool Registry
Manages all security tools with unified interface
Supports both direct MCP servers and Hexstrike MCP wrapper
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import os

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool categories"""
    NETWORK_SCANNING = "network_scanning"
    WEB_SCANNING = "web_scanning"
    DIRECTORY_ENUM = "directory_enumeration"
    SERVICE_ENUM = "service_enumeration"
    OSINT = "osint"
    EXPLOITATION = "exploitation"
    PASSWORD_CRACKING = "password_cracking"
    WIRELESS = "wireless"
    FORENSICS = "forensics"
    WEB_EXPLOITATION = "web_exploitation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    POST_EXPLOITATION = "post_exploitation"


class ToolStatus(str, Enum):
    """Tool availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    REQUIRES_CONFIG = "requires_config"


class ToolInfo:
    """Information about a security tool"""

    def __init__(
        self,
        name: str,
        category: ToolCategory,
        description: str,
        source: str,  # "mcp" or "hexstrike"
        wrapper_class: Optional[str] = None,
        binary_path: Optional[str] = None,
        requires_approval: bool = False,
        default_timeout: int = 300,
        metadata: Optional[Dict] = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.source = source
        self.wrapper_class = wrapper_class
        self.binary_path = binary_path
        self.requires_approval = requires_approval
        self.default_timeout = default_timeout
        self.metadata = metadata or {}
        self.status = ToolStatus.AVAILABLE

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "source": self.source,
            "wrapper_class": self.wrapper_class,
            "binary_path": self.binary_path,
            "requires_approval": self.requires_approval,
            "default_timeout": self.default_timeout,
            "status": self.status.value,
            "metadata": self.metadata
        }


class ToolRegistry:
    """
    Centralized registry for all security tools
    Manages both direct MCP tool servers and Hexstrike MCP integration
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize tool registry

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.tools: Dict[str, ToolInfo] = {}
        self.mcp_servers = {}
        self.hexstrike_client = None
        self.initialized = False

    async def initialize(
        self,
        mcp_servers: Optional[Dict] = None,
        hexstrike_client: Optional[Any] = None
    ):
        """
        Initialize tool registry with available tools

        Args:
            mcp_servers: Dictionary of direct MCP servers
            hexstrike_client: Hexstrike MCP client instance
        """
        logger.info("🔧 Initializing Tool Registry")

        self.mcp_servers = mcp_servers or {}
        self.hexstrike_client = hexstrike_client

        # Register direct MCP tools
        await self._register_mcp_tools()

        # Register Hexstrike tools
        if hexstrike_client and hexstrike_client.is_connected():
            await self._register_hexstrike_tools()

        # Verify tool availability
        await self._verify_tools()

        self.initialized = True
        logger.info(f"✅ Tool Registry initialized with {len(self.tools)} tools")

    async def _register_mcp_tools(self):
        """Register tools from direct MCP servers"""

        # Nmap
        if "nmap" in self.mcp_servers:
            self.register_tool(ToolInfo(
                name="nmap",
                category=ToolCategory.NETWORK_SCANNING,
                description="Network reconnaissance and port scanning",
                source="mcp",
                wrapper_class="NmapMCPServer",
                binary_path="/usr/bin/nmap",
                default_timeout=300
            ))

        # Nikto
        if "nikto" in self.mcp_servers:
            self.register_tool(ToolInfo(
                name="nikto",
                category=ToolCategory.WEB_SCANNING,
                description="Web vulnerability scanner",
                source="mcp",
                wrapper_class="NiktoMCPServer",
                binary_path="/usr/bin/nikto",
                default_timeout=600
            ))

        # SQLMap
        if "sqlmap" in self.mcp_servers:
            self.register_tool(ToolInfo(
                name="sqlmap",
                category=ToolCategory.WEB_EXPLOITATION,
                description="SQL injection testing tool",
                source="mcp",
                wrapper_class="SqlmapMCPServer",
                binary_path="/usr/bin/sqlmap",
                requires_approval=True,
                default_timeout=900
            ))

        # Gobuster
        if "gobuster" in self.mcp_servers:
            self.register_tool(ToolInfo(
                name="gobuster",
                category=ToolCategory.DIRECTORY_ENUM,
                description="Directory and file enumeration",
                source="mcp",
                wrapper_class="GobusterMCPServer",
                binary_path="/usr/bin/gobuster",
                default_timeout=300
            ))

    async def _register_hexstrike_tools(self):
        """Register tools from Hexstrike MCP"""
        if not self.hexstrike_client:
            return

        available_tools = self.hexstrike_client.get_available_tools()
        logger.info(f"📋 Registering {len(available_tools)} tools from Hexstrike MCP")

        # Define tool configurations
        hexstrike_configs = {
            # Network Scanning
            "masscan": (ToolCategory.NETWORK_SCANNING, "Fast port scanner", 300),
            "rustscan": (ToolCategory.NETWORK_SCANNING, "Modern port scanner", 300),
            "zmap": (ToolCategory.NETWORK_SCANNING, "Internet-wide scanner", 300),

            # Web Scanning
            "whatweb": (ToolCategory.WEB_SCANNING, "Web technology identifier", 180),
            "wpscan": (ToolCategory.WEB_SCANNING, "WordPress vulnerability scanner", 600),
            "nuclei": (ToolCategory.WEB_SCANNING, "Template-based scanner", 600),

            # Directory Enumeration
            "dirb": (ToolCategory.DIRECTORY_ENUM, "Web content scanner", 300),
            "dirbuster": (ToolCategory.DIRECTORY_ENUM, "Directory brute forcer", 300),
            "ffuf": (ToolCategory.DIRECTORY_ENUM, "Fast web fuzzer", 300),
            "feroxbuster": (ToolCategory.DIRECTORY_ENUM, "Content discovery", 300),

            # Service Enumeration
            "enum4linux": (ToolCategory.SERVICE_ENUM, "SMB enumeration tool", 300),
            "dnsenum": (ToolCategory.SERVICE_ENUM, "DNS enumeration", 180),
            "smbclient": (ToolCategory.SERVICE_ENUM, "SMB client", 180),

            # OSINT
            "theharvester": (ToolCategory.OSINT, "Email and domain harvester", 300),
            "shodan": (ToolCategory.OSINT, "Internet device scanner", 60),
            "amass": (ToolCategory.OSINT, "Subdomain enumeration", 600),
            "subfinder": (ToolCategory.OSINT, "Subdomain discovery", 300),
            "recon-ng": (ToolCategory.OSINT, "Reconnaissance framework", 300),

            # Exploitation
            "metasploit": (ToolCategory.EXPLOITATION, "Exploitation framework", 1800),
            "searchsploit": (ToolCategory.EXPLOITATION, "Exploit database search", 60),
            "exploitdb": (ToolCategory.EXPLOITATION, "Exploit database", 60),

            # Password Cracking
            "hashcat": (ToolCategory.PASSWORD_CRACKING, "Password cracker", 3600),
            "john": (ToolCategory.PASSWORD_CRACKING, "John the Ripper", 3600),
            "hydra": (ToolCategory.PASSWORD_CRACKING, "Network logon cracker", 1800),
            "medusa": (ToolCategory.PASSWORD_CRACKING, "Parallel login brute forcer", 1800),

            # Web Exploitation
            "burpsuite": (ToolCategory.WEB_EXPLOITATION, "Web security testing", 600),
            "owasp-zap": (ToolCategory.WEB_EXPLOITATION, "Web app scanner", 600),
            "xsser": (ToolCategory.WEB_EXPLOITATION, "XSS detection tool", 300),
            "commix": (ToolCategory.WEB_EXPLOITATION, "Command injection", 600),

            # Privilege Escalation
            "linpeas": (ToolCategory.PRIVILEGE_ESCALATION, "Linux privilege escalation", 300),
            "winpeas": (ToolCategory.PRIVILEGE_ESCALATION, "Windows privilege escalation", 300),
            "linux-exploit-suggester": (ToolCategory.PRIVILEGE_ESCALATION, "Linux exploit suggester", 60),
            "windows-exploit-suggester": (ToolCategory.PRIVILEGE_ESCALATION, "Windows exploit suggester", 60),

            # Post Exploitation
            "mimikatz": (ToolCategory.POST_EXPLOITATION, "Windows credential extraction", 180),
            "bloodhound": (ToolCategory.POST_EXPLOITATION, "AD attack path analysis", 600),
            "powersploit": (ToolCategory.POST_EXPLOITATION, "PowerShell post-exploitation", 300),
            "empire": (ToolCategory.POST_EXPLOITATION, "Post-exploitation framework", 600),

            # Wireless
            "aircrack-ng": (ToolCategory.WIRELESS, "Wireless security suite", 1800),
            "wifite": (ToolCategory.WIRELESS, "Automated wireless attack", 1800),
            "reaver": (ToolCategory.WIRELESS, "WPS attack tool", 1800),
        }

        # Register tools that are available in Hexstrike
        for tool_name in available_tools:
            if tool_name in hexstrike_configs:
                category, description, timeout = hexstrike_configs[tool_name]

                requires_approval = category in [
                    ToolCategory.EXPLOITATION,
                    ToolCategory.POST_EXPLOITATION,
                    ToolCategory.PASSWORD_CRACKING
                ]

                self.register_tool(ToolInfo(
                    name=tool_name,
                    category=category,
                    description=description,
                    source="hexstrike",
                    default_timeout=timeout,
                    requires_approval=requires_approval
                ))

    async def _verify_tools(self):
        """Verify tool availability"""
        for tool_name, tool_info in self.tools.items():
            if tool_info.source == "mcp":
                # Verify MCP server is available
                if tool_name not in self.mcp_servers:
                    tool_info.status = ToolStatus.UNAVAILABLE
                    logger.warning(f"⚠️ MCP server not available for {tool_name}")
            elif tool_info.source == "hexstrike":
                # Verify Hexstrike has this tool
                if not self.hexstrike_client or not self.hexstrike_client.is_connected():
                    tool_info.status = ToolStatus.UNAVAILABLE
                    logger.warning(f"⚠️ Hexstrike not available for {tool_name}")

    def register_tool(self, tool_info: ToolInfo):
        """Register a tool"""
        self.tools[tool_info.name] = tool_info
        logger.debug(f"Registered tool: {tool_info.name} ({tool_info.category.value})")

    def get_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """Get tool info by name"""
        return self.tools.get(tool_name)

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        status: Optional[ToolStatus] = None
    ) -> List[ToolInfo]:
        """
        List tools with optional filters

        Args:
            category: Filter by category
            status: Filter by status

        Returns:
            List of tool info objects
        """
        tools = list(self.tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if status:
            tools = [t for t in tools if t.status == status]

        return tools

    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get tool names in a category"""
        return [
            t.name for t in self.tools.values()
            if t.category == category and t.status == ToolStatus.AVAILABLE
        ]

    def get_tools_by_phase(self, phase: str) -> List[str]:
        """
        Get recommended tools for a specific phase

        Args:
            phase: Phase name (reconnaissance, enumeration, etc.)

        Returns:
            List of tool names
        """
        phase_tool_map = {
            "reconnaissance": [
                ToolCategory.NETWORK_SCANNING,
                ToolCategory.OSINT
            ],
            "enumeration": [
                ToolCategory.SERVICE_ENUM,
                ToolCategory.DIRECTORY_ENUM
            ],
            "vulnerability_scanning": [
                ToolCategory.WEB_SCANNING,
                ToolCategory.NETWORK_SCANNING
            ],
            "exploitation": [
                ToolCategory.EXPLOITATION,
                ToolCategory.WEB_EXPLOITATION
            ],
            "post_exploitation": [
                ToolCategory.POST_EXPLOITATION,
                ToolCategory.PRIVILEGE_ESCALATION
            ]
        }

        categories = phase_tool_map.get(phase, [])
        tools = []

        for category in categories:
            tools.extend(self.get_tools_by_category(category))

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict:
        """
        Execute a tool via appropriate interface

        Args:
            tool_name: Name of tool to execute
            params: Tool parameters

        Returns:
            Execution result dictionary
        """
        tool_info = self.get_tool(tool_name)

        if not tool_info:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": f"Tool '{tool_name}' not found in registry"
            }

        if tool_info.status != ToolStatus.AVAILABLE:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": f"Tool '{tool_name}' is not available (status: {tool_info.status.value})"
            }

        # Execute via appropriate source
        if tool_info.source == "mcp":
            return await self._execute_mcp_tool(tool_name, params)
        elif tool_info.source == "hexstrike":
            return await self._execute_hexstrike_tool(tool_name, params)
        else:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": f"Unknown tool source: {tool_info.source}"
            }

    async def _execute_mcp_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute tool via direct MCP server"""
        mcp_server = self.mcp_servers.get(tool_name)
        if not mcp_server:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": f"MCP server not found for {tool_name}"
            }

        try:
            result = await mcp_server.execute(params)
            return result
        except Exception as e:
            logger.error(f"MCP execution error ({tool_name}): {e}")
            return {
                "tool": tool_name,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_hexstrike_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute tool via Hexstrike MCP"""
        if not self.hexstrike_client:
            return {
                "tool": tool_name,
                "status": "failed",
                "error": "Hexstrike MCP client not initialized"
            }

        try:
            result = await self.hexstrike_client.execute_tool(tool_name, params)
            return result
        except Exception as e:
            logger.error(f"Hexstrike execution error ({tool_name}): {e}")
            return {
                "tool": tool_name,
                "status": "failed",
                "error": str(e)
            }

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        stats = {
            "total_tools": len(self.tools),
            "available": len([t for t in self.tools.values() if t.status == ToolStatus.AVAILABLE]),
            "unavailable": len([t for t in self.tools.values() if t.status == ToolStatus.UNAVAILABLE]),
            "by_category": {},
            "by_source": {"mcp": 0, "hexstrike": 0}
        }

        for category in ToolCategory:
            count = len([t for t in self.tools.values() if t.category == category])
            if count > 0:
                stats["by_category"][category.value] = count

        for tool in self.tools.values():
            stats["by_source"][tool.source] = stats["by_source"].get(tool.source, 0) + 1

        return stats

    def to_dict(self) -> Dict:
        """Export registry as dictionary"""
        return {
            "initialized": self.initialized,
            "tools": {name: tool.to_dict() for name, tool in self.tools.items()},
            "statistics": self.get_statistics()
        }
