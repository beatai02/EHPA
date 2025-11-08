"""
Enum4Linux MCP Server
SMB enumeration tool for Windows/Linux systems
"""

import json
import re
from typing import Dict, Any, List
from .base_server import BaseMCPServer


class Enum4LinuxMCPServer(BaseMCPServer):
    """MCP Server for enum4linux SMB enumeration tool"""

    def __init__(self):
        super().__init__(
            tool_name="enum4linux",
            description="SMB enumeration tool for Windows and Linux systems",
            binary_path="/usr/bin/enum4linux"
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        """Define the tool's input schema"""
        return {
            "type": "function",
            "function": {
                "name": "enum4linux",
                "description": "Enumerate SMB shares, users, groups, and system information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Target IP address or hostname"
                        },
                        "username": {
                            "type": "string",
                            "description": "Username for authentication (optional)"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for authentication (optional)"
                        },
                        "all": {
                            "type": "boolean",
                            "description": "Run all enumeration checks",
                            "default": True
                        },
                        "users": {
                            "type": "boolean",
                            "description": "Enumerate users",
                            "default": False
                        },
                        "shares": {
                            "type": "boolean",
                            "description": "Enumerate shares",
                            "default": False
                        },
                        "groups": {
                            "type": "boolean",
                            "description": "Enumerate groups",
                            "default": False
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
        if not self._is_valid_target(target):
            raise ValueError(f"Invalid target format: {target}")

        return True

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build enum4linux command"""
        target = params["target"]
        cmd_parts = [self.binary_path]

        # Authentication
        if "username" in params:
            cmd_parts.extend(["-u", params["username"]])
        if "password" in params:
            cmd_parts.extend(["-p", params["password"]])

        # Enumeration options
        if params.get("all", True):
            cmd_parts.append("-a")
        else:
            if params.get("users"):
                cmd_parts.append("-U")
            if params.get("shares"):
                cmd_parts.append("-S")
            if params.get("groups"):
                cmd_parts.append("-G")

        cmd_parts.append(target)

        return " ".join(cmd_parts)

    def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse enum4linux output"""
        result = {
            "target": params["target"],
            "users": [],
            "shares": [],
            "groups": [],
            "domain_info": {},
            "os_info": {},
            "vulnerabilities": []
        }

        lines = output.split('\n')

        # Parse users
        in_users_section = False
        for line in lines:
            if "Users on" in line or "user:" in line.lower():
                in_users_section = True
            elif in_users_section:
                user_match = re.search(r'user:\[(.*?)\]', line)
                if user_match:
                    result["users"].append(user_match.group(1))

        # Parse shares
        for line in lines:
            share_match = re.search(r'Sharename.*?Type.*?Comment', line, re.IGNORECASE)
            if share_match:
                idx = lines.index(line)
                for share_line in lines[idx+1:]:
                    if share_line.strip() and not share_line.startswith('---'):
                        parts = share_line.split()
                        if len(parts) >= 2:
                            result["shares"].append({
                                "name": parts[0],
                                "type": parts[1] if len(parts) > 1 else "Unknown"
                            })
                    else:
                        break

        # Parse OS information
        os_match = re.search(r'OS=\[(.*?)\].*?Server=\[(.*?)\]', output, re.DOTALL)
        if os_match:
            result["os_info"] = {
                "os": os_match.group(1).strip(),
                "server": os_match.group(2).strip()
            }

        # Parse domain information
        domain_match = re.search(r'Domain Name: (.*?)$', output, re.MULTILINE)
        if domain_match:
            result["domain_info"]["name"] = domain_match.group(1).strip()

        # Check for common vulnerabilities
        if "NT_STATUS_ACCESS_DENIED" not in output:
            if result["shares"]:
                for share in result["shares"]:
                    if share["name"].lower() in ["c$", "admin$", "ipc$"]:
                        result["vulnerabilities"].append({
                            "title": f"Administrative share accessible: {share['name']}",
                            "severity": "high",
                            "description": f"Administrative share {share['name']} is accessible"
                        })

        if "guest account" in output.lower() and "disabled" not in output.lower():
            result["vulnerabilities"].append({
                "title": "Guest account enabled",
                "severity": "medium",
                "description": "Guest account is enabled on the target system"
            })

        return result
