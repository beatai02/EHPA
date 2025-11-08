"""
WPScan MCP Server
WordPress vulnerability scanner
"""

import json
from typing import Dict, Any, List
from .base_server import BaseMCPServer


class WPScanMCPServer(BaseMCPServer):
    """MCP Server for WPScan WordPress vulnerability scanner"""

    def __init__(self):
        super().__init__(
            tool_name="wpscan",
            description="WordPress vulnerability scanner",
            binary_path="/usr/bin/wpscan"
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        """Define the tool's input schema"""
        return {
            "type": "function",
            "function": {
                "name": "wpscan",
                "description": "Scan WordPress websites for vulnerabilities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "WordPress site URL"
                        },
                        "enumerate": {
                            "type": "string",
                            "description": "Enumeration mode: vp (vulnerable plugins), ap (all plugins), vt (vulnerable themes), u (users)",
                            "default": "vp,vt,u"
                        },
                        "api_token": {
                            "type": "string",
                            "description": "WPVulnDB API token for vulnerability data"
                        },
                        "plugins_detection": {
                            "type": "string",
                            "enum": ["passive", "aggressive", "mixed"],
                            "description": "Plugin detection mode",
                            "default": "passive"
                        },
                        "random_user_agent": {
                            "type": "boolean",
                            "description": "Use random user agent",
                            "default": True
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        if "url" not in params:
            raise ValueError("URL is required")

        url = params["url"]
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")

        return True

    def build_command(self, params: Dict[str, Any]) -> str:
        """Build wpscan command"""
        url = params["url"]
        cmd_parts = [self.binary_path]

        # Target URL
        cmd_parts.extend(["--url", url])

        # JSON output
        cmd_parts.extend(["--format", "json"])

        # Enumeration
        enumerate = params.get("enumerate", "vp,vt,u")
        cmd_parts.extend(["--enumerate", enumerate])

        # API token
        if "api_token" in params:
            cmd_parts.extend(["--api-token", params["api_token"]])

        # Plugin detection mode
        plugins_detection = params.get("plugins_detection", "passive")
        cmd_parts.extend(["--plugins-detection", plugins_detection])

        # Random user agent
        if params.get("random_user_agent", True):
            cmd_parts.append("--random-user-agent")

        # Disable SSL verification for testing
        cmd_parts.append("--disable-tls-checks")

        return " ".join(cmd_parts)

    def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse wpscan JSON output"""
        result = {
            "url": params["url"],
            "wordpress_version": None,
            "theme": None,
            "plugins": [],
            "users": [],
            "vulnerabilities": [],
            "total_vulnerabilities": 0
        }

        try:
            data = json.loads(output)

            # WordPress version
            if "version" in data:
                result["wordpress_version"] = {
                    "number": data["version"].get("number"),
                    "status": data["version"].get("status"),
                    "vulnerabilities": len(data["version"].get("vulnerabilities", []))
                }

                # WordPress core vulnerabilities
                for vuln in data["version"].get("vulnerabilities", []):
                    result["vulnerabilities"].append({
                        "title": vuln.get("title", "WordPress Core Vulnerability"),
                        "type": "wordpress_core",
                        "fixed_in": vuln.get("fixed_in"),
                        "references": vuln.get("references", {}),
                        "severity": "high"
                    })
                    result["total_vulnerabilities"] += 1

            # Theme information
            if "main_theme" in data:
                theme_data = data["main_theme"]
                result["theme"] = {
                    "name": theme_data.get("slug"),
                    "version": theme_data.get("version", {}).get("number"),
                    "vulnerabilities": len(theme_data.get("vulnerabilities", []))
                }

                # Theme vulnerabilities
                for vuln in theme_data.get("vulnerabilities", []):
                    result["vulnerabilities"].append({
                        "title": vuln.get("title", "Theme Vulnerability"),
                        "type": "theme",
                        "theme": theme_data.get("slug"),
                        "fixed_in": vuln.get("fixed_in"),
                        "references": vuln.get("references", {}),
                        "severity": "medium"
                    })
                    result["total_vulnerabilities"] += 1

            # Plugins
            if "plugins" in data:
                for plugin_slug, plugin_data in data["plugins"].items():
                    plugin_info = {
                        "name": plugin_slug,
                        "version": plugin_data.get("version", {}).get("number"),
                        "vulnerabilities": len(plugin_data.get("vulnerabilities", []))
                    }
                    result["plugins"].append(plugin_info)

                    # Plugin vulnerabilities
                    for vuln in plugin_data.get("vulnerabilities", []):
                        result["vulnerabilities"].append({
                            "title": vuln.get("title", "Plugin Vulnerability"),
                            "type": "plugin",
                            "plugin": plugin_slug,
                            "fixed_in": vuln.get("fixed_in"),
                            "references": vuln.get("references", {}),
                            "severity": "high"
                        })
                        result["total_vulnerabilities"] += 1

            # Users
            if "users" in data:
                for user_id, user_data in data["users"].items():
                    result["users"].append({
                        "id": user_id,
                        "username": user_data.get("username"),
                        "found_by": user_data.get("found_by")
                    })

                # User enumeration finding
                if result["users"]:
                    result["vulnerabilities"].append({
                        "title": "User Enumeration Possible",
                        "type": "configuration",
                        "description": f"Found {len(result['users'])} users via enumeration",
                        "severity": "low",
                        "users": [u["username"] for u in result["users"]]
                    })

        except json.JSONDecodeError as e:
            result["parse_error"] = str(e)

        return result
