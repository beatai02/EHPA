"""
Nmap MCP Server
Network reconnaissance and port scanning tool
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

from .base_server import BaseMCPServer


class NmapMCPServer(BaseMCPServer):
    """
    Nmap tool server for network reconnaissance

    Capabilities:
    - Host discovery
    - Port scanning
    - Service version detection
    - OS detection
    - Script scanning
    """

    def __init__(self):
        super().__init__('nmap')

    def get_tool_schema(self) -> Dict[str, Any]:
        """Return Nmap tool schema"""
        return {
            'name': 'nmap',
            'description': 'Network reconnaissance and port scanning',
            'parameters': {
                'target': {
                    'type': 'string',
                    'required': True,
                    'description': 'Target IP address or domain'
                },
                'ports': {
                    'type': 'string',
                    'required': False,
                    'description': 'Port specification (e.g., "1-1000", "80,443", "-")',
                    'default': '1-1000'
                },
                'scan_type': {
                    'type': 'string',
                    'required': False,
                    'description': 'Scan type: syn, tcp, udp, service',
                    'default': 'service'
                },
                'aggressive': {
                    'type': 'boolean',
                    'required': False,
                    'description': 'Enable aggressive scanning (OS, version, scripts)',
                    'default': False
                },
                'timing': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Timing template (0-5): 0=paranoid, 5=insane',
                    'default': 4
                },
                'custom_flags': {
                    'type': 'string',
                    'required': False,
                    'description': 'Additional custom nmap flags'
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Nmap parameters"""
        if 'target' not in params:
            return False, "Target is required"

        target = params['target']
        if not target or not isinstance(target, str):
            return False, "Target must be a non-empty string"

        # Basic validation - no shell injection characters
        dangerous_chars = [';', '&&', '|', '`', '$']
        for char in dangerous_chars:
            if char in target:
                return False, f"Target contains invalid character: {char}"

        # Validate timing if provided
        timing = params.get('timing', 4)
        if not isinstance(timing, int) or timing < 0 or timing > 5:
            return False, "Timing must be an integer between 0 and 5"

        return True, None

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build Nmap command from parameters"""
        target = params['target']
        ports = params.get('ports', '1-1000')
        scan_type = params.get('scan_type', 'service')
        aggressive = params.get('aggressive', False)
        timing = params.get('timing', 4)
        custom_flags = params.get('custom_flags', '')

        command_parts = []

        # Scan type flags
        if scan_type == 'syn':
            command_parts.append('-sS')
        elif scan_type == 'tcp':
            command_parts.append('-sT')
        elif scan_type == 'udp':
            command_parts.append('-sU')
        elif scan_type == 'service':
            command_parts.append('-sV')

        # Port specification
        if ports == '-':
            command_parts.append('-p-')  # All ports
        else:
            command_parts.append(f'-p{ports}')

        # Timing
        command_parts.append(f'-T{timing}')

        # Aggressive mode
        if aggressive:
            command_parts.append('-A')  # OS detection, version, scripts, traceroute
        else:
            command_parts.append('-sC')  # Default scripts only

        # Output format (XML for easier parsing)
        command_parts.append('-oX -')  # Output XML to stdout

        # Custom flags
        if custom_flags:
            command_parts.append(custom_flags)

        # Target (always last)
        command_parts.append(target)

        return ' '.join(command_parts)

    async def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Nmap output (XML format)

        Extracts:
        - IP addresses
        - Open ports
        - Services and versions
        - OS detection
        - Vulnerabilities from scripts
        """
        result = {
            'hosts': [],
            'open_ports': [],
            'services': {},
            'os_detection': None,
            'vulnerabilities': [],
            'summary': ''
        }

        try:
            # Parse XML output
            # Remove any non-XML content before parsing
            xml_start = output.find('<?xml')
            if xml_start == -1:
                xml_start = output.find('<nmaprun')

            if xml_start != -1:
                xml_output = output[xml_start:]
                root = ET.fromstring(xml_output)

                # Parse hosts
                for host in root.findall('.//host'):
                    host_info = self._parse_host(host)
                    result['hosts'].append(host_info)

                    # Aggregate open ports and services
                    for port_info in host_info.get('ports', []):
                        port = port_info['port']
                        result['open_ports'].append(port)
                        result['services'][port] = port_info.get('service', 'unknown')

                # Parse OS detection
                os_match = root.find('.//osmatch')
                if os_match is not None:
                    result['os_detection'] = os_match.get('name')

                # Generate summary
                result['summary'] = self._generate_summary(result)

            else:
                # Fallback to text parsing
                result = self._parse_text_output(output)

        except Exception as e:
            self.logger.error(f"Failed to parse XML output: {e}")
            # Fallback to text parsing
            result = self._parse_text_output(output)

        return result

    def _parse_host(self, host_element: ET.Element) -> Dict[str, Any]:
        """Parse individual host from XML"""
        host_info = {
            'ip': '',
            'hostname': '',
            'status': '',
            'ports': [],
            'os': None
        }

        # IP address
        address = host_element.find('.//address[@addrtype="ipv4"]')
        if address is not None:
            host_info['ip'] = address.get('addr', '')

        # Hostname
        hostname = host_element.find('.//hostname')
        if hostname is not None:
            host_info['hostname'] = hostname.get('name', '')

        # Status
        status = host_element.find('.//status')
        if status is not None:
            host_info['status'] = status.get('state', '')

        # Ports
        for port in host_element.findall('.//port'):
            port_info = self._parse_port(port)
            if port_info:
                host_info['ports'].append(port_info)

        # OS
        osmatch = host_element.find('.//osmatch')
        if osmatch is not None:
            host_info['os'] = osmatch.get('name')

        return host_info

    def _parse_port(self, port_element: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse individual port from XML"""
        port_id = port_element.get('portid')
        protocol = port_element.get('protocol')

        state = port_element.find('.//state')
        if state is None or state.get('state') != 'open':
            return None

        service = port_element.find('.//service')

        port_info = {
            'port': int(port_id),
            'protocol': protocol,
            'state': 'open',
            'service': '',
            'version': '',
            'product': ''
        }

        if service is not None:
            port_info['service'] = service.get('name', '')
            port_info['product'] = service.get('product', '')
            port_info['version'] = service.get('version', '')

            # Build full version string
            version_parts = []
            if port_info['product']:
                version_parts.append(port_info['product'])
            if port_info['version']:
                version_parts.append(port_info['version'])
            port_info['full_version'] = ' '.join(version_parts)

        # Check for script results (vulnerabilities)
        scripts = port_element.findall('.//script')
        if scripts:
            port_info['scripts'] = []
            for script in scripts:
                script_id = script.get('id')
                script_output = script.get('output')
                port_info['scripts'].append({
                    'id': script_id,
                    'output': script_output
                })

                # Check for vulnerability scripts
                if 'vuln' in script_id.lower():
                    # This might be a vulnerability
                    port_info['potential_vulnerability'] = True

        return port_info

    def _parse_text_output(self, output: str) -> Dict[str, Any]:
        """Fallback text parsing for Nmap output"""
        result = {
            'open_ports': [],
            'services': {},
            'summary': 'Text-based parsing (limited information)'
        }

        lines = output.split('\n')

        # Look for open port lines
        port_pattern = r'(\d+)/(tcp|udp)\s+open\s+(\S+)'
        for line in lines:
            match = re.search(port_pattern, line)
            if match:
                port = int(match.group(1))
                service = match.group(3)
                result['open_ports'].append(port)
                result['services'][port] = service

        return result

    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        parts = []

        num_hosts = len(result.get('hosts', []))
        num_ports = len(result.get('open_ports', []))

        parts.append(f"Scanned {num_hosts} host(s)")
        parts.append(f"Found {num_ports} open port(s)")

        if result.get('os_detection'):
            parts.append(f"OS: {result['os_detection']}")

        return '. '.join(parts)
