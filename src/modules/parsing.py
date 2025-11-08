"""
Parsing Module - Security Data Analyst
Output parsing and data extraction using Claude LLM
Responsible for interpreting tool outputs and extracting findings
"""

import json
import logging
from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic

from ..core.config import config
from ..utils.logger import get_logger


class ParsingModule:
    """
    Parsing Module acts as a Security Data Analyst
    Uses Claude LLM for intelligent output parsing and interpretation

    Responsibilities:
    - Parse raw tool outputs
    - Extract structured security findings
    - Identify vulnerabilities from scan results
    - Classify severity levels
    - Extract target information (IPs, ports, services)
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = AsyncAnthropic(api_key=config.settings.anthropic_api_key)
        self.model = config.llm.model
        self.max_tokens = 2048
        self.temperature = 0.3  # Low temperature for precise extraction

        # Get system prompt from config
        self.system_prompt = config.get_module_prompt('parsing')
        if not self.system_prompt:
            self.system_prompt = self._get_default_system_prompt()

        self.logger.info("Parsing module initialized")

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for parsing module"""
        return """You are a security data analyst expert in parsing penetration testing tool outputs.

Your expertise includes interpreting outputs from:
- Nmap: Network scans and service detection
- Nikto: Web vulnerability scans
- SQLMap: SQL injection testing
- Gobuster: Directory enumeration
- Metasploit: Exploitation attempts

Your role is DATA EXTRACTION AND INTERPRETATION:
- Parse raw tool outputs into structured data
- Identify security vulnerabilities and findings
- Classify severity levels accurately
- Extract technical details (IPs, ports, services, versions)
- Distinguish between vulnerabilities and informational findings

Severity Classification:
- CRITICAL: Remote code execution, authentication bypass, full system compromise
- HIGH: SQL injection, XSS, sensitive data exposure, privilege escalation
- MEDIUM: Information disclosure, outdated software with known vulns, misconfigurations
- LOW: Minor issues, recommendations, low-impact findings
- INFORMATIONAL: Technology detection, open ports (context-dependent), general info

Always respond in valid JSON format as specified in prompts.
Be thorough but avoid false positives."""

    async def parse_tool_output(
        self,
        tool: str,
        output: str,
        target: str
    ) -> Dict[str, Any]:
        """
        Parse raw tool output and extract structured findings

        Args:
            tool: Tool name that generated the output
            output: Raw tool output
            target: Target being tested

        Returns:
            Dictionary with parsed vulnerabilities and findings
        """
        self.logger.info(f"Parsing {tool} output for target: {target}")

        # Truncate very long outputs
        truncated_output = output[:8000] if len(output) > 8000 else output

        prompt = f"""Parse this {tool} output and extract all security findings.

TOOL: {tool}
TARGET: {target}

OUTPUT:
{truncated_output}

Extract ALL findings and structure them appropriately:

VULNERABILITIES: Security issues that could be exploited
- Must have: title, description, severity, evidence
- Optional: cvss_score, cve_id, port, service, url, remediation

FINDINGS: General discoveries (open ports, technologies, configurations)
- Must have: category, title, description
- Optional: Any relevant data

TARGET INFO: Technical information about target
- ip_addresses, open_ports, services (port->service mapping), technologies, operating_system, web_server

Respond with ONLY valid JSON in this EXACT format:
{{
  "vulnerabilities": [
    {{
      "title": "Clear vulnerability title",
      "description": "Detailed description",
      "severity": "critical/high/medium/low/informational",
      "cvss_score": 7.5,
      "cve_id": "CVE-XXXX-XXXXX",
      "target": "{target}",
      "port": 80,
      "service": "http",
      "url": "http://example.com/path",
      "evidence": "Relevant output showing vulnerability",
      "remediation": "How to fix",
      "references": ["url1", "url2"],
      "discovered_by": "{tool}",
      "verified": false,
      "exploitable": true
    }}
  ],
  "findings": [
    {{
      "category": "open_port/technology_detected/misconfiguration/etc",
      "title": "Finding title",
      "description": "Finding description",
      "target": "{target}",
      "data": {{"key": "value"}},
      "discovered_by": "{tool}"
    }}
  ],
  "ip_addresses": ["x.x.x.x"],
  "open_ports": [80, 443],
  "services": {{"80": "http", "443": "https"}},
  "technologies": ["Apache", "PHP"],
  "operating_system": "Linux",
  "web_server": "Apache/2.4.41",
  "summary": "Brief summary of what was discovered"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            self.logger.debug(f"LLM response: {content[:200]}...")

            # Parse JSON response
            result = self._parse_json_response(content)

            # Validate and enhance vulnerabilities
            vulns = result.get('vulnerabilities', [])
            findings = result.get('findings', [])

            self.logger.info(
                f"Parsed {len(vulns)} vulnerabilities and {len(findings)} findings"
            )

            # Ensure required fields in vulnerabilities
            for vuln in vulns:
                vuln.setdefault('target', target)
                vuln.setdefault('discovered_by', tool)
                vuln.setdefault('verified', False)
                vuln.setdefault('exploitable', False)

            # Ensure required fields in findings
            for finding in findings:
                finding.setdefault('target', target)
                finding.setdefault('discovered_by', tool)
                finding.setdefault('data', {})

            return result

        except Exception as e:
            self.logger.error(f"Failed to parse tool output: {e}", exc_info=True)
            # Return fallback parsing
            return self._fallback_parse(tool, output, target)

    async def extract_vulnerabilities(
        self,
        output: str,
        tool: str,
        target: str
    ) -> List[Dict[str, Any]]:
        """
        Focus specifically on extracting vulnerabilities from output

        Args:
            output: Raw tool output
            tool: Tool name
            target: Target being tested

        Returns:
            List of vulnerability dictionaries
        """
        self.logger.info(f"Extracting vulnerabilities from {tool} output")

        result = await self.parse_tool_output(tool, output, target)
        return result.get('vulnerabilities', [])

    async def classify_severity(
        self,
        vulnerability_description: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Classify the severity of a vulnerability

        Args:
            vulnerability_description: Description of the vulnerability
            context: Additional context

        Returns:
            Dictionary with severity classification and CVSS score
        """
        self.logger.info("Classifying vulnerability severity")

        prompt = f"""Classify the severity of this vulnerability.

VULNERABILITY:
{vulnerability_description}

CONTEXT:
{context}

Consider:
- Exploitability: How easy to exploit?
- Impact: What can attacker achieve?
- Scope: What systems affected?
- Attack complexity: Required conditions?

Respond with ONLY valid JSON:
{{
  "severity": "critical/high/medium/low/informational",
  "cvss_score": 0.0-10.0,
  "reasoning": "Explanation of classification",
  "exploitability": "easy/medium/hard",
  "impact": "Description of potential impact"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            return result

        except Exception as e:
            self.logger.error(f"Failed to classify severity: {e}", exc_info=True)
            return {
                "severity": "medium",
                "cvss_score": 5.0,
                "reasoning": "Default classification due to parsing error"
            }

    async def extract_target_info(
        self,
        output: str,
        tool: str
    ) -> Dict[str, Any]:
        """
        Extract technical target information from output

        Args:
            output: Raw tool output
            tool: Tool name

        Returns:
            Dictionary with target information
        """
        self.logger.info(f"Extracting target info from {tool} output")

        truncated_output = output[:5000] if len(output) > 5000 else output

        prompt = f"""Extract technical information about the target from this {tool} output.

OUTPUT:
{truncated_output}

Extract:
- IP addresses
- Open ports
- Services and versions
- Technologies detected
- Operating system
- Web server information

Respond with ONLY valid JSON:
{{
  "ip_addresses": ["list"],
  "open_ports": [80, 443],
  "services": {{"80": "http", "443": "https"}},
  "technologies": ["Apache", "PHP"],
  "operating_system": "Linux 4.x",
  "web_server": "Apache/2.4.41"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            return result

        except Exception as e:
            self.logger.error(f"Failed to extract target info: {e}", exc_info=True)
            return {}

    def _fallback_parse(self, tool: str, output: str, target: str) -> Dict[str, Any]:
        """
        Fallback parsing using simple pattern matching
        Used when LLM parsing fails
        """
        self.logger.info("Using fallback parsing")

        result = {
            "vulnerabilities": [],
            "findings": [],
            "ip_addresses": [],
            "open_ports": [],
            "services": {},
            "technologies": [],
            "summary": "Fallback parsing - limited extraction"
        }

        # Simple pattern matching for common outputs
        lines = output.split('\n')

        # Extract open ports (common across tools)
        import re
        port_pattern = r'(\d+)/(tcp|udp)\s+open'
        for line in lines:
            match = re.search(port_pattern, line)
            if match:
                port = int(match.group(1))
                if port not in result['open_ports']:
                    result['open_ports'].append(port)
                    result['findings'].append({
                        "category": "open_port",
                        "title": f"Open port {port}",
                        "description": line.strip(),
                        "target": target,
                        "data": {"port": port},
                        "discovered_by": tool
                    })

        # Look for common vulnerability keywords
        vuln_keywords = [
            'vulnerability', 'vulnerable', 'exploit', 'injection',
            'xss', 'sql', 'rce', 'authentication bypass'
        ]

        for line in lines:
            line_lower = line.lower()
            for keyword in vuln_keywords:
                if keyword in line_lower:
                    result['vulnerabilities'].append({
                        "title": f"Potential {keyword.upper()} detected",
                        "description": line.strip(),
                        "severity": "medium",
                        "target": target,
                        "evidence": line.strip(),
                        "discovered_by": tool,
                        "verified": False,
                        "exploitable": False
                    })
                    break

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        content = content.strip()

        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.debug(f"Content: {content[:500]}")
            # Try to extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except:
                    pass
            return {}
