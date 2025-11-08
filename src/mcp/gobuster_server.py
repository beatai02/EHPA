"""
Gobuster MCP Server
Directory and file enumeration tool
"""

import re
from typing import Dict, Any, Optional, List

from .base_server import BaseMCPServer


class GobusterMCPServer(BaseMCPServer):
    """
    Gobuster tool server for directory/file enumeration

    Capabilities:
    - Directory enumeration
    - File enumeration
    - Virtual host enumeration
    - DNS subdomain enumeration
    """

    def __init__(self):
        super().__init__('gobuster')

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return Gobuster tool schema"""
        return {
            'name': 'gobuster',
            'description': 'Directory and file enumeration tool',
            'parameters': {
                'target': {
                    'type': 'string',
                    'required': True,
                    'description': 'Target URL'
                },
                'mode': {
                    'type': 'string',
                    'required': False,
                    'description': 'Mode: dir, dns, vhost',
                    'default': 'dir'
                },
                'wordlist': {
                    'type': 'string',
                    'required': False,
                    'description': 'Path to wordlist file',
                    'default': '/usr/share/wordlists/dirb/common.txt'
                },
                'extensions': {
                    'type': 'string',
                    'required': False,
                    'description': 'File extensions to check (comma-separated)',
                    'default': ''
                },
                'threads': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Number of concurrent threads',
                    'default': 10
                },
                'status_codes': {
                    'type': 'string',
                    'required': False,
                    'description': 'Status codes to include (comma-separated)',
                    'default': '200,204,301,302,307,401,403'
                },
                'timeout': {
                    'type': 'integer',
                    'required': False,
                    'description': 'HTTP timeout in seconds',
                    'default': 10
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Gobuster parameters"""
        if 'target' not in params:
            return False, "Target URL is required"

        target = params['target']
        if not target or not isinstance(target, str):
            return False, "Target must be a non-empty string"

        mode = params.get('mode', 'dir')
        if mode not in ['dir', 'dns', 'vhost']:
            return False, "Mode must be one of: dir, dns, vhost"

        threads = params.get('threads', 10)
        if not isinstance(threads, int) or threads < 1 or threads > 100:
            return False, "Threads must be between 1 and 100"

        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build Gobuster command from parameters"""
        target = params['target']
        mode = params.get('mode', 'dir')
        wordlist = params.get('wordlist', '/usr/share/wordlists/dirb/common.txt')
        extensions = params.get('extensions', '')
        threads = params.get('threads', 10)
        status_codes = params.get('status_codes', '200,204,301,302,307,401,403')
        timeout = params.get('timeout', 10)

        command_parts = [mode]

        # Mode-specific parameters
        if mode == 'dir':
            command_parts.append(f'-u {target}')
            command_parts.append(f'-w {wordlist}')

            if extensions:
                command_parts.append(f'-x {extensions}')

            command_parts.append(f'-s {status_codes}')

        elif mode == 'dns':
            # DNS mode expects just domain, not full URL
            domain = target.replace('http://', '').replace('https://', '').split('/')[0]
            command_parts.append(f'-d {domain}')
            command_parts.append(f'-w {wordlist}')

        elif mode == 'vhost':
            command_parts.append(f'-u {target}')
            command_parts.append(f'-w {wordlist}')

        # Common parameters
        command_parts.append(f'-t {threads}')
        command_parts.append(f'--timeout {timeout}s')

        # Quiet mode (less verbose)
        command_parts.append('-q')

        # No errors in output
        command_parts.append('-n')

        return ' '.join(command_parts)

    async def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gobuster output

        Extracts:
        - Discovered directories and files
        - Status codes
        - Sizes
        """
        result = {
            'discovered': [],
            'directories': [],
            'files': [],
            'findings': [],
            'summary': ''
        }

        target = params['target']
        mode = params.get('mode', 'dir')
        lines = output.split('\n')

        if mode == 'dir':
            # Directory mode output format:
            # /path (Status: 200) [Size: 1234]
            pattern = r'(/\S+)\s+\(Status:\s+(\d+)\)(?:\s+\[Size:\s+(\d+)\])?'

            for line in lines:
                match = re.search(pattern, line)
                if match:
                    path = match.group(1)
                    status = int(match.group(2))
                    size = int(match.group(3)) if match.group(3) else 0

                    item = {
                        'path': path,
                        'status': status,
                        'size': size,
                        'url': f"{target.rstrip('/')}{path}"
                    }

                    result['discovered'].append(item)

                    # Classify as directory or file
                    if path.endswith('/'):
                        result['directories'].append(item)
                    else:
                        result['files'].append(item)

                    # Create finding
                    category = 'directory' if path.endswith('/') else 'file'
                    severity = self._determine_severity(path, status)

                    finding = {
                        'category': f'{category}_found',
                        'title': f"Discovered {category}: {path}",
                        'description': f"Found {category} with status {status}",
                        'target': target,
                        'data': item
                    }

                    # If interesting, create a potential vulnerability
                    if severity != 'informational':
                        finding['severity'] = severity
                        finding['interesting'] = True

                    result['findings'].append(finding)

        elif mode == 'dns':
            # DNS mode output format:
            # Found: subdomain.domain.com
            pattern = r'Found:\s+(\S+)'

            for line in lines:
                match = re.search(pattern, line)
                if match:
                    subdomain = match.group(1)

                    item = {
                        'subdomain': subdomain,
                        'type': 'dns'
                    }

                    result['discovered'].append(item)

                    result['findings'].append({
                        'category': 'subdomain_found',
                        'title': f"Discovered subdomain: {subdomain}",
                        'description': f"DNS enumeration found subdomain",
                        'target': target,
                        'data': item
                    })

        # Generate summary
        num_discovered = len(result['discovered'])
        if mode == 'dir':
            result['summary'] = f"Discovered {len(result['directories'])} directories and {len(result['files'])} files"
        elif mode == 'dns':
            result['summary'] = f"Discovered {num_discovered} subdomains"
        else:
            result['summary'] = f"Discovered {num_discovered} items"

        return result

    def _determine_severity(self, path: str, status: int) -> str:
        """
        Determine if a discovered path is interesting/potentially vulnerable

        Returns: severity level or 'informational'
        """
        path_lower = path.lower()

        # High severity paths
        high_severity_paths = [
            'admin', 'administrator', 'config', 'backup',
            '.git', '.svn', '.env', 'database', 'db',
            'sql', 'dump', 'private', 'secret'
        ]

        for sensitive in high_severity_paths:
            if sensitive in path_lower:
                return 'high' if status == 200 else 'medium'

        # Medium severity paths
        medium_severity_paths = [
            'upload', 'uploads', 'files', 'download',
            'api', 'test', 'dev', 'debug', 'console'
        ]

        for interesting in medium_severity_paths:
            if interesting in path_lower:
                return 'medium' if status == 200 else 'low'

        # Informational
        return 'informational'
