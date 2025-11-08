"""
Nikto MCP Server
Web vulnerability scanner
"""

import json
import re
from typing import Dict, Any, Optional, List

from .base_server import BaseMCPServer


class NiktoMCPServer(BaseMCPServer):
    """
    Nikto tool server for web vulnerability scanning

    Capabilities:
    - Web server fingerprinting
    - Vulnerability detection
    - Configuration testing
    - Security header analysis
    """

    def __init__(self):
        super().__init__('nikto')
        # Override timeout - Nikto can take a while
        self.max_timeout = 600

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return Nikto tool schema"""
        return {
            'name': 'nikto',
            'description': 'Web vulnerability scanner',
            'parameters': {
                'target': {
                    'type': 'string',
                    'required': True,
                    'description': 'Target URL or IP address'
                },
                'port': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Port number',
                    'default': 80
                },
                'ssl': {
                    'type': 'boolean',
                    'required': False,
                    'description': 'Use SSL/TLS',
                    'default': False
                },
                'tuning': {
                    'type': 'string',
                    'required': False,
                    'description': 'Tuning options (e.g., "x" for all tests)',
                    'default': 'x'
                },
                'timeout': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Request timeout in seconds',
                    'default': 10
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Nikto parameters"""
        if 'target' not in params:
            return False, "Target is required"

        target = params['target']
        if not target or not isinstance(target, str):
            return False, "Target must be a non-empty string"

        # Validate port if provided
        port = params.get('port')
        if port is not None:
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, "Port must be between 1 and 65535"

        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build Nikto command from parameters"""
        target = params['target']
        port = params.get('port', 80)
        ssl = params.get('ssl', False)
        tuning = params.get('tuning', 'x')
        timeout = params.get('timeout', 10)

        command_parts = []

        # Target and port
        # Nikto expects -h host:port or just -h host
        if ssl:
            target_url = f"https://{target}:{port}"
        else:
            target_url = f"http://{target}:{port}"

        command_parts.append(f'-h {target_url}')

        # Tuning
        command_parts.append(f'-Tuning {tuning}')

        # Timeout
        command_parts.append(f'-timeout {timeout}')

        # Output format JSON (if supported)
        # Note: Older Nikto versions might not support JSON
        command_parts.append('-Format json')

        # No interactive prompts
        command_parts.append('-ask no')

        return ' '.join(command_parts)

    async def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Nikto output

        Extracts:
        - Discovered vulnerabilities
        - Server information
        - Security headers
        - Interesting findings
        """
        result = {
            'server_info': {},
            'vulnerabilities': [],
            'findings': [],
            'summary': ''
        }

        try:
            # Try to parse as JSON first
            if output.strip().startswith('{'):
                json_result = json.loads(output)
                result = self._parse_json_output(json_result, params)
            else:
                # Fallback to text parsing
                result = self._parse_text_output(output, params)

        except json.JSONDecodeError:
            # Not JSON, use text parsing
            result = self._parse_text_output(output, params)
        except Exception as e:
            self.logger.error(f"Failed to parse Nikto output: {e}")
            result['summary'] = f"Parsing error: {e}"

        return result

    def _parse_json_output(self, json_data: Dict, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Nikto JSON output"""
        result = {
            'server_info': {},
            'vulnerabilities': [],
            'findings': [],
            'summary': ''
        }

        target = params['target']

        # Extract server info
        if 'host' in json_data:
            result['server_info'] = {
                'ip': json_data.get('host'),
                'hostname': json_data.get('hostname', target),
                'port': json_data.get('port'),
                'banner': json_data.get('banner', '')
            }

        # Extract vulnerabilities from items
        items = json_data.get('items', [])
        for item in items:
            # Nikto findings
            osvdb_id = item.get('OSVDB', '')
            method = item.get('method', 'GET')
            uri = item.get('uri', '/')
            description = item.get('msg', '')

            # Determine severity based on OSVDB and description
            severity = self._determine_severity(description)

            if severity in ['critical', 'high', 'medium']:
                # This is a vulnerability
                result['vulnerabilities'].append({
                    'title': f"Nikto finding: {uri}",
                    'description': description,
                    'severity': severity,
                    'uri': uri,
                    'method': method,
                    'osvdb_id': osvdb_id,
                    'target': target
                })
            else:
                # This is a general finding
                result['findings'].append({
                    'category': 'web_finding',
                    'title': f"Web finding: {uri}",
                    'description': description,
                    'uri': uri,
                    'method': method,
                    'target': target
                })

        # Generate summary
        result['summary'] = f"Found {len(result['vulnerabilities'])} vulnerabilities and {len(result['findings'])} findings"

        return result

    def _parse_text_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Nikto text output"""
        result = {
            'server_info': {},
            'vulnerabilities': [],
            'findings': [],
            'summary': ''
        }

        target = params['target']
        lines = output.split('\n')

        # Extract server banner
        for line in lines:
            if 'Server:' in line:
                server_match = re.search(r'Server:\s+(.+)', line)
                if server_match:
                    result['server_info']['banner'] = server_match.group(1).strip()

        # Extract findings
        # Nikto format: + OSVDB-####: /path: Description
        finding_pattern = r'\+\s+(?:OSVDB-(\d+):\s+)?(.+?):\s+(.+)'

        for line in lines:
            match = re.search(finding_pattern, line)
            if match:
                osvdb_id = match.group(1) or ''
                uri = match.group(2).strip()
                description = match.group(3).strip()

                severity = self._determine_severity(description)

                if severity in ['critical', 'high', 'medium']:
                    result['vulnerabilities'].append({
                        'title': f"Nikto finding: {uri}",
                        'description': description,
                        'severity': severity,
                        'uri': uri,
                        'osvdb_id': osvdb_id,
                        'target': target
                    })
                else:
                    result['findings'].append({
                        'category': 'web_finding',
                        'title': f"Web finding: {uri}",
                        'description': description,
                        'uri': uri,
                        'target': target
                    })

        # Count findings
        total_vulns = len(result['vulnerabilities'])
        total_findings = len(result['findings'])
        result['summary'] = f"Nikto scan complete: {total_vulns} vulnerabilities, {total_findings} findings"

        return result

    def _determine_severity(self, description: str) -> str:
        """
        Determine severity level based on finding description

        Returns: critical, high, medium, low, or informational
        """
        description_lower = description.lower()

        # Critical keywords
        critical_keywords = [
            'remote code execution', 'rce', 'arbitrary code',
            'authentication bypass', 'unrestricted file upload'
        ]
        for keyword in critical_keywords:
            if keyword in description_lower:
                return 'critical'

        # High keywords
        high_keywords = [
            'sql injection', 'xss', 'cross-site scripting',
            'path traversal', 'directory traversal', 'lfi', 'rfi',
            'command injection', 'xxe', 'sensitive'
        ]
        for keyword in high_keywords:
            if keyword in description_lower:
                return 'high'

        # Medium keywords
        medium_keywords = [
            'vulnerable', 'misconfiguration', 'outdated',
            'deprecated', 'weak', 'insecure', 'exposed'
        ]
        for keyword in medium_keywords:
            if keyword in description_lower:
                return 'medium'

        # Low keywords
        low_keywords = [
            'information disclosure', 'banner', 'version'
        ]
        for keyword in low_keywords:
            if keyword in description_lower:
                return 'low'

        # Default to informational
        return 'informational'
