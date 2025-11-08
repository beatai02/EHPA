"""
Enumeration Tools MCP Servers
Wrappers for additional enumeration tools: dnsenum, ffuf, feroxbuster

These wrappers use Hexstrike MCP for unified tool execution
"""

import logging
from typing import Dict, Any, List, Optional
from .base_server import BaseMCPServer

logger = logging.getLogger(__name__)


class DNSEnumMCPServer(BaseMCPServer):
    """
    DNSenum MCP Server
    DNS enumeration tool for discovering DNS records
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "dnsenum"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate dnsenum parameters"""
        if 'domain' not in params:
            return False, "Missing required parameter: domain"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build dnsenum command"""
        domain = params['domain']
        enum_all = params.get('enum_all', True)
        threads = params.get('threads', 5)

        cmd = f"dnsenum --threads {threads}"

        if enum_all:
            cmd += " --enum"

        cmd += f" {domain}"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dnsenum via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing dnsenum via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('dnsenum', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse dnsenum output"""
        records = {
            'A': [],
            'MX': [],
            'NS': [],
            'TXT': [],
            'CNAME': [],
            'SOA': []
        }

        subdomains = []

        lines = output.split('\n')
        for line in lines:
            line = line.strip()

            # Parse record types
            for record_type in records.keys():
                if f'{record_type} Record' in line or line.startswith(record_type):
                    # Extract record value
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        records[record_type].append(value)

            # Parse subdomains
            if 'Brute forcing with' in line or line.startswith(domain := params.get('domain', '')):
                if domain in line:
                    subdomains.append(line)

        return {
            'records': records,
            'subdomains': subdomains,
            'total_records': sum(len(v) for v in records.values()),
            'raw_output': output
        }


class FFUFMCPServer(BaseMCPServer):
    """
    FFUF MCP Server
    Fast web fuzzer for directory and parameter discovery
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "ffuf"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate ffuf parameters"""
        if 'url' not in params:
            return False, "Missing required parameter: url"
        if 'wordlist' not in params:
            return False, "Missing required parameter: wordlist"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build ffuf command"""
        url = params['url']
        wordlist = params['wordlist']
        extensions = params.get('extensions', '')
        threads = params.get('threads', 40)
        match_status = params.get('match_status', '200,204,301,302,307,401,403')
        timeout = params.get('timeout', 10)

        # Ensure URL has FUZZ keyword
        if 'FUZZ' not in url:
            url = url.rstrip('/') + '/FUZZ'

        cmd = f"ffuf -u {url} -w {wordlist} -t {threads} -mc {match_status} -timeout {timeout}"

        if extensions:
            cmd += f" -e {extensions}"

        # Silent mode for easier parsing
        cmd += " -s"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ffuf via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing ffuf via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('ffuf', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse ffuf output"""
        import json

        discovered = []

        # Try JSON parsing
        try:
            data = json.loads(output)
            if 'results' in data:
                for result in data['results']:
                    discovered.append({
                        'url': result.get('url', ''),
                        'status': result.get('status', 0),
                        'length': result.get('length', 0),
                        'words': result.get('words', 0),
                        'lines': result.get('lines', 0)
                    })
        except json.JSONDecodeError:
            # Fallback to text parsing
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    discovered.append({'path': line.strip()})

        return {
            'discovered': discovered,
            'count': len(discovered),
            'directories': [d for d in discovered if not '.' in d.get('url', d.get('path', '')).split('/')[-1]],
            'files': [d for d in discovered if '.' in d.get('url', d.get('path', '')).split('/')[-1]]
        }


class FeroxbusterMCPServer(BaseMCPServer):
    """
    Feroxbuster MCP Server
    Fast, simple, recursive content discovery tool
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "feroxbuster"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate feroxbuster parameters"""
        if 'url' not in params:
            return False, "Missing required parameter: url"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build feroxbuster command"""
        url = params['url']
        wordlist = params.get('wordlist', '/usr/share/seclists/Discovery/Web-Content/common.txt')
        threads = params.get('threads', 50)
        depth = params.get('depth', 4)
        extensions = params.get('extensions', 'php,html,txt,js')

        cmd = f"feroxbuster -u {url} -w {wordlist} -t {threads} -d {depth}"

        if extensions:
            cmd += f" -x {extensions}"

        # Quiet mode
        cmd += " -q"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feroxbuster via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing feroxbuster via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('feroxbuster', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse feroxbuster output"""
        discovered = []

        lines = output.split('\n')
        for line in lines:
            # Format: STATUS_CODE SIZE URL
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    status = int(parts[0])
                    size = parts[1]
                    url = parts[2]

                    discovered.append({
                        'status': status,
                        'size': size,
                        'url': url,
                        'type': 'file' if '.' in url.split('/')[-1] else 'directory'
                    })
                except (ValueError, IndexError):
                    pass

        return {
            'discovered': discovered,
            'count': len(discovered),
            'directories': [d for d in discovered if d['type'] == 'directory'],
            'files': [d for d in discovered if d['type'] == 'file']
        }


class DirbMCPServer(BaseMCPServer):
    """
    Dirb MCP Server
    Classic web content scanner
    """

    def __init__(self, hexstrike_client=None):
        super().__init__()
        self.hexstrike_client = hexstrike_client

    @property
    def tool_name(self) -> str:
        return "dirb"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate dirb parameters"""
        if 'url' not in params:
            return False, "Missing required parameter: url"
        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build dirb command"""
        url = params['url']
        wordlist = params.get('wordlist', '/usr/share/wordlists/dirb/common.txt')
        extensions = params.get('extensions', '')

        cmd = f"dirb {url} {wordlist}"

        if extensions:
            cmd += f" -X .{extensions.replace(',', ',.')}"

        # Silent mode
        cmd += " -S"

        return cmd

    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dirb via Hexstrike if available"""
        if self.hexstrike_client and self.hexstrike_client.is_connected():
            logger.info("Executing dirb via Hexstrike MCP")
            return await self.hexstrike_client.execute_tool('dirb', params)
        else:
            logger.warning("Hexstrike not available, using direct execution")
            return await self._execute_direct(command)

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse dirb output"""
        discovered = []

        lines = output.split('\n')
        for line in lines:
            if line.startswith('+ ') or line.startswith('==> DIRECTORY:'):
                # Extract URL and status
                if '(CODE:' in line:
                    url = line.split()[1]
                    status_start = line.find('CODE:') + 5
                    status_end = line.find('|', status_start)
                    status = int(line[status_start:status_end].strip())

                    discovered.append({
                        'url': url,
                        'status': status,
                        'type': 'directory' if 'DIRECTORY' in line else 'file'
                    })

        return {
            'discovered': discovered,
            'count': len(discovered),
            'directories': [d for d in discovered if d.get('type') == 'directory'],
            'files': [d for d in discovered if d.get('type') == 'file']
        }
