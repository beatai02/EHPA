"""
Nuclei MCP Server
Template-based vulnerability scanner
"""

import json
from typing import Dict, Any, List
from .base_server import BaseMCPServer


class NucleiMCPServer(BaseMCPServer):
    """MCP Server for Nuclei vulnerability scanner"""

    def __init__(self):
        super().__init__(
            tool_name="nuclei",
            description="Fast and customizable vulnerability scanner based on templates",
            binary_path="/usr/bin/nuclei"
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        """Define the tool's input schema"""
        return {
            "type": "function",
            "function": {
                "name": "nuclei",
                "description": "Scan targets for vulnerabilities using Nuclei templates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Target URL or IP address"
                        },
                        "templates": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific templates to use (optional)"
                        },
                        "severity": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low", "info"]
                            },
                            "description": "Filter by severity levels"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter templates by tags (e.g., xss, sqli, cve)"
                        },
                        "rate_limit": {
                            "type": "integer",
                            "description": "Maximum requests per second",
                            "default": 150
                        }
                    },
                    "required": ["target"]
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        if "target" not in params:
            raise ValueError("Target is required")

        target = params["target"]
        if not self._is_valid_url(target) and not self._is_valid_target(target):
            raise ValueError(f"Invalid target format: {target}")

        return True

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build nuclei command"""
        target = params["target"]
        cmd_parts = [self.binary_path]

        # Target
        cmd_parts.extend(["-u", target])

        # JSON output
        cmd_parts.extend(["-json", "-o", "/tmp/nuclei_output.json"])

        # Templates
        if "templates" in params:
            for template in params["templates"]:
                cmd_parts.extend(["-t", template])

        # Severity filter
        if "severity" in params:
            severities = ",".join(params["severity"])
            cmd_parts.extend(["-s", severities])

        # Tags filter
        if "tags" in params:
            tags = ",".join(params["tags"])
            cmd_parts.extend(["-tags", tags])

        # Rate limit
        rate_limit = params.get("rate_limit", 150)
        cmd_parts.extend(["-rl", str(rate_limit)])

        # Silent mode (reduce output)
        cmd_parts.append("-silent")

        return " ".join(cmd_parts)

    def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse nuclei JSON output"""
        result = {
            "target": params["target"],
            "vulnerabilities": [],
            "total_findings": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        }

        # Parse JSON lines
        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                finding = json.loads(line)

                vuln = {
                    "title": finding.get("info", {}).get("name", "Unknown"),
                    "description": finding.get("info", {}).get("description", ""),
                    "severity": finding.get("info", {}).get("severity", "info").lower(),
                    "matched_at": finding.get("matched-at", ""),
                    "template_id": finding.get("template-id", ""),
                    "type": finding.get("type", ""),
                    "tags": finding.get("info", {}).get("tags", []),
                    "reference": finding.get("info", {}).get("reference", []),
                    "cve_id": finding.get("info", {}).get("classification", {}).get("cve-id", [])
                }

                result["vulnerabilities"].append(vuln)
                result["total_findings"] += 1

                severity = vuln["severity"]
                if severity in result["by_severity"]:
                    result["by_severity"][severity] += 1

            except json.JSONDecodeError:
                continue

        return result
