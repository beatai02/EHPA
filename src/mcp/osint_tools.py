"""
OSINT Tools MCP Servers
Wrappers for OSINT tools: amass, subfinder, theharvester, shodan

These wrappers use Hexstrike MCP for unified tool execution
"""

import logging
from typing import Dict, Any, List, Optional
from .base_server import BaseMCPServer

logger = logging.getLogger(__name__)


class AmassMCPServer(BaseMCPServer):
    """
    Amass MCP Server
    Subdomain enumeration and OSINT tool
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "amass"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate amass parameters"""
        if 'domain' not in params:
            return False, "Missing required parameter: domain"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build amass command"""
        domain = params['domain']
        passive = params.get('passive', True)
        timeout = params.get('timeout', 300)

        if passive:
            cmd = f"amass enum -passive -d {domain} -timeout {timeout}"
        else:
            cmd = f"amass enum -d {domain} -timeout {timeout}"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute amass via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing amass via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('amass', params)
        else:
            # Fallback to direct execution
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse amass output"""
        subdomains = []

        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                subdomains.append(line)

        return {
            'subdomains': subdomains,
            'count': len(subdomains)
        }


class SubfinderMCPServer(BaseMCPServer):
    """
    Subfinder MCP Server
    Fast subdomain discovery tool
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "subfinder"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate subfinder parameters"""
        if 'domain' not in params:
            return False, "Missing required parameter: domain"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build subfinder command"""
        domain = params['domain']
        silent = params.get('silent', True)
        all_sources = params.get('all', False)

        cmd = f"subfinder -d {domain}"

        if silent:
            cmd += " -silent"
        if all_sources:
            cmd += " -all"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute subfinder via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing subfinder via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('subfinder', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse subfinder output"""
        subdomains = []

        for line in output.split('\n'):
            line = line.strip()
            if line:
                subdomains.append(line)

        return {
            'subdomains': subdomains,
            'count': len(subdomains)
        }


class TheHarvesterMCPServer(BaseMCPServer):
    """
    TheHarvester MCP Server
    OSINT tool for gathering emails, names, subdomains
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "theharvester"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate theHarvester parameters"""
        if 'domain' not in params:
            return False, "Missing required parameter: domain"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build theHarvester command"""
        domain = params['domain']
        sources = params.get('sources', ['google', 'bing'])
        limit = params.get('limit', 500)

        sources_str = ','.join(sources) if isinstance(sources, list) else sources

        cmd = f"theHarvester -d {domain} -b {sources_str} -l {limit}"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute theHarvester via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing theHarvester via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('theharvester', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse theHarvester output"""
        emails = []
        hosts = []
        ips = []

        in_emails = False
        in_hosts = False
        in_ips = False

        for line in output.split('\n'):
            line = line.strip()

            if '[*] Emails found:' in line:
                in_emails = True
                in_hosts = False
                in_ips = False
                continue
            elif '[*] Hosts found:' in line:
                in_emails = False
                in_hosts = True
                in_ips = False
                continue
            elif '[*] IPs found:' in line:
                in_emails = False
                in_hosts = False
                in_ips = True
                continue

            if in_emails and '@' in line:
                emails.append(line)
            elif in_hosts and line and not line.startswith('['):
                hosts.append(line)
            elif in_ips and line and not line.startswith('['):
                ips.append(line)

        return {
            'emails': emails,
            'hosts': hosts,
            'ips': ips,
            'email_count': len(emails),
            'host_count': len(hosts),
            'ip_count': len(ips)
        }


class ShodanMCPServer(BaseMCPServer):
    """
    Shodan MCP Server
    Search engine for Internet-connected devices
    """

    def __init__(self, hexstrike_client=None, api_key: Optional[str] = None):
        super().__init__()
        self.hexstrike_client = hexstrike_client
        self.api_key = api_key

    @property
    def tool_name(self) -> str:
        return "shodan"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate shodan parameters"""
        if 'query' not in params and 'host' not in params:
            return False, "Missing required parameter: query or host"

        if not self.api_key:
            return False, "Shodan API key not configured"

        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build shodan command"""
        if 'host' in params:
            cmd = f"shodan host {params['host']}"
        else:
            query = params['query']
            cmd = f"shodan search {query}"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shodan via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing shodan via Hexstrike MCP")
            # Pass API key in params
            params['api_key'] = self.api_key
            return await self.hexstrike_client.execute_tool('shodan', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse shodan output"""
        # Shodan output is usually JSON
        import json

        try:
            data = json.loads(output)
            return {
                'results': data,
                'count': len(data) if isinstance(data, list) else 1
            }
        except json.JSONDecodeError:
            # Fallback to text parsing
            return {
                'output': output,
                'parsed': False
            }
