"""
Command Parser - Parse natural language into structured commands
Extracts intent, entities, and parameters from user messages
"""

import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..utils.logger import get_logger


@dataclass
class ParsedCommand:
    """Structured command representation"""
    action: str  # scan, run_tool, show, test, etc.
    target: Optional[str] = None
    tool: Optional[str] = None
    parameters: Dict[str, Any] = None
    raw_input: str = ""
    confidence: float = 0.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class CommandParser:
    """
    Parse natural language commands into structured actions

    Examples:
    - "Scan target.com" -> {action: "scan", target: "target.com"}
    - "Run nmap on port 80" -> {action: "run_tool", tool: "nmap", parameters: {"port": 80}}
    - "Show results" -> {action: "show", parameters: {"type": "results"}}
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # Define command patterns
        self.patterns = self._build_patterns()

        # Tool name mapping
        self.tool_names = [
            'nmap', 'nikto', 'sqlmap', 'gobuster', 'metasploit', 'nuclei',
            'subfinder', 'amass', 'ffuf', 'hydra', 'john', 'hashcat',
            'burp', 'wireshark', 'aircrack', 'masscan'
        ]

        # Action keywords
        self.action_keywords = {
            'scan': ['scan', 'reconnaissance', 'recon', 'enumerate', 'discover'],
            'run_tool': ['run', 'execute', 'use', 'launch', 'start'],
            'show': ['show', 'display', 'get', 'list', 'view'],
            'test': ['test', 'check', 'verify', 'validate', 'exploit'],
            'explain': ['explain', 'what is', 'how does', 'tell me about', 'describe'],
            'stop': ['stop', 'halt', 'cancel', 'abort', 'terminate'],
            'help': ['help', 'assist', 'guide'],
            'report': ['report', 'summarize', 'generate report']
        }

        self.logger.info("Command Parser initialized")

    def parse(self, user_input: str) -> ParsedCommand:
        """
        Parse user input into structured command

        Args:
            user_input: Natural language command

        Returns:
            ParsedCommand object with extracted information
        """
        user_input = user_input.strip()
        self.logger.debug(f"Parsing command: {user_input}")

        # Try pattern matching first
        for pattern_name, pattern_info in self.patterns.items():
            match = re.search(pattern_info['regex'], user_input, re.IGNORECASE)
            if match:
                command = self._extract_from_match(match, pattern_info, user_input)
                self.logger.debug(f"Matched pattern: {pattern_name}")
                return command

        # Fallback to keyword-based parsing
        command = self._parse_by_keywords(user_input)

        return command

    def _build_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build regex patterns for command recognition"""
        return {
            # Scan patterns
            'scan_target': {
                'regex': r'scan\s+(?:target\s+)?([a-zA-Z0-9\.\-]+)',
                'action': 'scan',
                'extract': {'target': 1}
            },
            'scan_target_alt': {
                'regex': r'(?:start|begin|initiate)\s+(?:a\s+)?scan\s+(?:of|on|for)\s+([a-zA-Z0-9\.\-]+)',
                'action': 'scan',
                'extract': {'target': 1}
            },

            # Run tool patterns
            'run_tool': {
                'regex': r'run\s+(\w+)\s+(?:on|against)\s+([a-zA-Z0-9\.\-]+)',
                'action': 'run_tool',
                'extract': {'tool': 1, 'target': 2}
            },
            'run_tool_simple': {
                'regex': r'run\s+(\w+)',
                'action': 'run_tool',
                'extract': {'tool': 1}
            },

            # Test patterns
            'test_vulnerability': {
                'regex': r'test\s+(?:for\s+)?([a-z\s]+)(?:\s+on\s+([a-zA-Z0-9\.\-]+))?',
                'action': 'test',
                'extract': {'vulnerability_type': 1, 'target': 2}
            },

            # Show patterns
            'show_results': {
                'regex': r'show\s+(?:me\s+)?(?:the\s+)?(results|findings|vulnerabilities|status|progress)',
                'action': 'show',
                'extract': {'type': 1}
            },

            # Explain patterns
            'explain_concept': {
                'regex': r'(?:what\s+is|explain|describe|tell\s+me\s+about)\s+(.+)',
                'action': 'explain',
                'extract': {'concept': 1}
            },

            # Port specification
            'scan_port': {
                'regex': r'(?:scan|check)\s+port\s+(\d+)\s+on\s+([a-zA-Z0-9\.\-]+)',
                'action': 'scan',
                'extract': {'port': 1, 'target': 2}
            },

            # Stop command
            'stop_scan': {
                'regex': r'(?:stop|halt|cancel|abort)',
                'action': 'stop',
                'extract': {}
            },

            # Help command
            'help': {
                'regex': r'(?:help|what\s+can\s+you\s+do|capabilities)',
                'action': 'help',
                'extract': {}
            },

            # Generate report
            'generate_report': {
                'regex': r'(?:generate|create|make)\s+(?:a\s+)?report',
                'action': 'report',
                'extract': {}
            }
        }

    def _extract_from_match(
        self,
        match: re.Match,
        pattern_info: Dict[str, Any],
        raw_input: str
    ) -> ParsedCommand:
        """Extract command from regex match"""
        command = ParsedCommand(
            action=pattern_info['action'],
            raw_input=raw_input,
            confidence=0.9
        )

        # Extract captured groups
        for key, group_num in pattern_info['extract'].items():
            value = match.group(group_num)
            if value:
                value = value.strip()

                # Handle different parameter types
                if key == 'target':
                    command.target = value
                elif key == 'tool':
                    command.tool = self._normalize_tool_name(value)
                elif key == 'port':
                    command.parameters['port'] = int(value)
                elif key == 'type':
                    command.parameters['type'] = value
                elif key == 'concept':
                    command.parameters['concept'] = value
                elif key == 'vulnerability_type':
                    command.parameters['vulnerability_type'] = value

        return command

    def _parse_by_keywords(self, user_input: str) -> ParsedCommand:
        """Fallback parsing using keyword matching"""
        user_input_lower = user_input.lower()

        # Determine action
        action = 'unknown'
        max_matches = 0

        for act, keywords in self.action_keywords.items():
            matches = sum(1 for kw in keywords if kw in user_input_lower)
            if matches > max_matches:
                max_matches = matches
                action = act

        command = ParsedCommand(
            action=action,
            raw_input=user_input,
            confidence=0.5 if max_matches > 0 else 0.3
        )

        # Extract target (domain/IP pattern)
        target_match = re.search(
            r'\b(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3}\b',
            user_input
        )
        if target_match:
            command.target = target_match.group(0)

        # Extract tool name
        for tool in self.tool_names:
            if tool in user_input_lower:
                command.tool = tool
                break

        # Extract port number
        port_match = re.search(r'port\s+(\d+)', user_input_lower)
        if port_match:
            command.parameters['port'] = int(port_match.group(1))

        return command

    def _normalize_tool_name(self, tool_name: str) -> str:
        """Normalize tool name to standard format"""
        tool_name = tool_name.lower().strip()

        # Handle common variations
        tool_mapping = {
            'metasploit': 'metasploit',
            'msf': 'metasploit',
            'msfconsole': 'metasploit',
            'burpsuite': 'burp',
            'burp suite': 'burp',
            'wireshark': 'wireshark',
            'tshark': 'wireshark',
            'john': 'john',
            'john the ripper': 'john'
        }

        return tool_mapping.get(tool_name, tool_name)

    def extract_targets(self, text: str) -> List[str]:
        """Extract all potential targets from text"""
        # Match domains
        domains = re.findall(
            r'\b(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}\b',
            text
        )

        # Match IPs
        ips = re.findall(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            text
        )

        return list(set(domains + ips))

    def extract_ports(self, text: str) -> List[int]:
        """Extract port numbers from text"""
        ports = re.findall(r'\b(\d{1,5})\b', text)
        return [int(p) for p in ports if 0 < int(p) <= 65535]

    def is_command(self, text: str) -> bool:
        """Check if text appears to be a command"""
        command = self.parse(text)
        return command.action != 'unknown' and command.confidence > 0.4

    def get_action_type(self, text: str) -> str:
        """Get the primary action type from text"""
        command = self.parse(text)
        return command.action
