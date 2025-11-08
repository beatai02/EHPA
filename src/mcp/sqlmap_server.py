"""
SQLMap MCP Server
SQL injection testing tool
"""

import json
import re
from typing import Dict, Any, Optional, List

from .base_server import BaseMCPServer


class SQLMapMCPServer(BaseMCPServer):
    """
    SQLMap tool server for SQL injection testing

    Capabilities:
    - SQL injection detection
    - Database enumeration
    - Data extraction
    - File system access testing
    """

    def __init__(self):
        super().__init__('sqlmap')
        # SQLMap can take a very long time
        self.max_timeout = 900  # 15 minutes

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return SQLMap tool schema"""
        return {
            'name': 'sqlmap',
            'description': 'SQL injection testing tool',
            'parameters': {
                'target': {
                    'type': 'string',
                    'required': True,
                    'description': 'Target URL with injectable parameter'
                },
                'data': {
                    'type': 'string',
                    'required': False,
                    'description': 'POST data string'
                },
                'cookie': {
                    'type': 'string',
                    'required': False,
                    'description': 'HTTP Cookie header value'
                },
                'level': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Testing level (1-5)',
                    'default': 1
                },
                'risk': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Risk level (1-3)',
                    'default': 1
                },
                'technique': {
                    'type': 'string',
                    'required': False,
                    'description': 'SQL injection techniques to use (BEUSTQ)',
                    'default': 'BEUST'
                },
                'enum_dbs': {
                    'type': 'boolean',
                    'required': False,
                    'description': 'Enumerate databases',
                    'default': False
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate SQLMap parameters"""
        if 'target' not in params:
            return False, "Target URL is required"

        target = params['target']
        if not target or not isinstance(target, str):
            return False, "Target must be a non-empty string"

        # Basic URL validation
        if not target.startswith(('http://', 'https://')):
            return False, "Target must be a valid HTTP/HTTPS URL"

        # Validate level if provided
        level = params.get('level', 1)
        if not isinstance(level, int) or level < 1 or level > 5:
            return False, "Level must be an integer between 1 and 5"

        # Validate risk if provided
        risk = params.get('risk', 1)
        if not isinstance(risk, int) or risk < 1 or risk > 3:
            return False, "Risk must be an integer between 1 and 3"

        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build SQLMap command from parameters"""
        target = params['target']
        data = params.get('data')
        cookie = params.get('cookie')
        level = params.get('level', 1)
        risk = params.get('risk', 1)
        technique = params.get('technique', 'BEUST')
        enum_dbs = params.get('enum_dbs', False)

        command_parts = []

        # Target URL
        command_parts.append(f'-u "{target}"')

        # POST data
        if data:
            command_parts.append(f'--data="{data}"')

        # Cookie
        if cookie:
            command_parts.append(f'--cookie="{cookie}"')

        # Level and Risk
        command_parts.append(f'--level={level}')
        command_parts.append(f'--risk={risk}')

        # Techniques
        command_parts.append(f'--technique={technique}')

        # Batch mode (non-interactive)
        command_parts.append('--batch')

        # Random user agent
        command_parts.append('--random-agent')

        # Output format
        command_parts.append('--flush-session')  # Fresh scan
        command_parts.append('--fresh-queries')

        # Database enumeration
        if enum_dbs:
            command_parts.append('--dbs')

        # Threads for faster scanning
        command_parts.append('--threads=5')

        return ' '.join(command_parts)

    async def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse SQLMap output

        Extracts:
        - SQL injection vulnerabilities
        - Database information
        - Backend DBMS
        - Injection points
        """
        result = {
            'vulnerable': False,
            'injection_points': [],
            'dbms': None,
            'databases': [],
            'vulnerabilities': [],
            'summary': ''
        }

        target = params['target']
        lines = output.split('\n')

        # Check if vulnerable
        if 'is vulnerable' in output.lower() or 'parameter is vulnerable' in output.lower():
            result['vulnerable'] = True

        # Extract DBMS
        dbms_pattern = r'back-end DBMS:\s+(.+)'
        for line in lines:
            match = re.search(dbms_pattern, line, re.IGNORECASE)
            if match:
                result['dbms'] = match.group(1).strip()
                break

        # Extract injection type and parameter
        parameter_pattern = r'Parameter:\s+(.+?)\s+\((.+?)\)'
        type_pattern = r'Type:\s+(.+)'
        title_pattern = r'Title:\s+(.+)'
        payload_pattern = r'Payload:\s+(.+)'

        current_injection = {}
        for line in lines:
            param_match = re.search(parameter_pattern, line)
            if param_match:
                if current_injection:
                    result['injection_points'].append(current_injection)
                current_injection = {
                    'parameter': param_match.group(1).strip(),
                    'type': param_match.group(2).strip(),
                    'injection_type': '',
                    'title': '',
                    'payload': ''
                }

            type_match = re.search(type_pattern, line)
            if type_match and current_injection:
                current_injection['injection_type'] = type_match.group(1).strip()

            title_match = re.search(title_pattern, line)
            if title_match and current_injection:
                current_injection['title'] = title_match.group(1).strip()

            payload_match = re.search(payload_pattern, line)
            if payload_match and current_injection:
                current_injection['payload'] = payload_match.group(1).strip()

        if current_injection:
            result['injection_points'].append(current_injection)

        # Extract databases
        if 'available databases' in output.lower():
            in_db_section = False
            for line in lines:
                if 'available databases' in line.lower():
                    in_db_section = True
                    continue
                if in_db_section:
                    # Database names are usually listed with [*]
                    db_match = re.search(r'\[\*\]\s+(.+)', line)
                    if db_match:
                        result['databases'].append(db_match.group(1).strip())
                    elif line.strip() == '':
                        break

        # Create vulnerabilities from injection points
        for injection in result['injection_points']:
            vuln = {
                'title': f"SQL Injection in parameter '{injection.get('parameter', 'unknown')}'",
                'description': injection.get('title', 'SQL injection vulnerability detected'),
                'severity': 'high',
                'parameter': injection.get('parameter'),
                'injection_type': injection.get('injection_type'),
                'payload': injection.get('payload'),
                'target': target,
                'dbms': result.get('dbms'),
                'evidence': f"SQLMap detected {injection.get('injection_type')} in {injection.get('parameter')}",
                'remediation': 'Use parameterized queries or prepared statements to prevent SQL injection',
                'cvss_score': 8.5
            }
            result['vulnerabilities'].append(vuln)

        # Generate summary
        if result['vulnerable']:
            num_injections = len(result['injection_points'])
            summary_parts = [
                f"SQL injection found in {num_injections} parameter(s)"
            ]
            if result['dbms']:
                summary_parts.append(f"Backend DBMS: {result['dbms']}")
            if result['databases']:
                summary_parts.append(f"Found {len(result['databases'])} database(s)")
            result['summary'] = '. '.join(summary_parts)
        else:
            result['summary'] = "No SQL injection vulnerabilities detected"

        return result
