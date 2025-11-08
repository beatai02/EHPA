"""
Generation Module - Tactical Security Engineer
Command generation and tactical execution using Claude LLM
Responsible for creating specific tool commands and payloads
"""

import json
import logging
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic

from ..core.config import config
from ..utils.logger import get_logger


class GenerationModule:
    """
    Generation Module acts as a Tactical Security Engineer
    Uses Claude LLM for command generation and tactical planning

    Responsibilities:
    - Generate specific tool commands
    - Create exploitation payloads
    - Provide detailed execution instructions
    - Suggest appropriate tool flags and options
    - Explain expected outputs
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = AsyncAnthropic(api_key=config.settings.anthropic_api_key)
        self.model = config.llm.model
        self.max_tokens = 1024
        self.temperature = 0.5  # Lower temperature for more precise commands

        # Get system prompt from config
        self.system_prompt = config.get_module_prompt('generation')
        if not self.system_prompt:
            self.system_prompt = self._get_default_system_prompt()

        self.logger.info("Generation module initialized")

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for generation module"""
        return """You are an expert security engineer specializing in penetration testing tools.

Your expertise includes:
- Nmap: Network reconnaissance and port scanning
- Nikto: Web vulnerability scanning
- SQLMap: SQL injection testing
- Gobuster: Directory and file enumeration
- Metasploit: Exploitation framework

Your role is TACTICAL COMMAND GENERATION:
- Generate precise, safe, and effective commands
- Validate all targets are within authorized scope
- Use appropriate flags and options for each tool
- Explain what each command does and why
- Predict expected outputs
- Suggest follow-up actions based on results

Command generation principles:
1. Safety: Never generate destructive commands without explicit authorization
2. Stealth: Use appropriate timing and rate-limiting to avoid detection
3. Efficiency: Optimize scan parameters for speed vs thoroughness
4. Accuracy: Ensure commands are syntactically correct
5. Context: Consider previous findings when generating commands

Always respond in valid JSON format as specified in prompts."""

    async def generate_command(
        self,
        tool: str,
        target: str,
        context: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Generate a specific command for a penetration testing tool

        Args:
            tool: Tool name (nmap, nikto, sqlmap, gobuster, metasploit)
            target: Target domain/IP
            context: Current session context
            task_description: Description of what the task should accomplish

        Returns:
            Dictionary with command, explanation, and expected output
        """
        self.logger.info(f"Generating {tool} command for target: {target}")

        # Get tool configuration
        tool_config = config.get_tool_config(tool)
        default_flags = tool_config.get('default_flags', [])

        prompt = f"""Generate a specific {tool} command for this penetration testing task.

TASK: {task_description}
TARGET: {target}
TOOL: {tool}
DEFAULT FLAGS: {' '.join(default_flags) if default_flags else 'None'}

CONTEXT:
{context[:1000]}

Requirements:
1. Generate the exact command to run
2. Use appropriate flags for this specific task
3. Ensure the command is safe and within scope
4. Optimize for effectiveness and stealth

For {tool}, consider:
{self._get_tool_specific_guidance(tool)}

Respond with ONLY valid JSON:
{{
  "command": "exact command without the tool name (just arguments)",
  "full_command": "complete command including tool name",
  "explanation": "What this command does and why these flags",
  "expected_output": "What we expect to discover",
  "estimated_duration": "rough time estimate",
  "warnings": ["any", "safety", "considerations"]
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

            self.logger.info(f"Generated command: {result.get('full_command', 'N/A')}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to generate command: {e}", exc_info=True)
            # Return fallback command
            return self._get_fallback_command(tool, target)

    async def create_exploit_payload(
        self,
        vulnerability: Dict[str, Any],
        target: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Generate exploitation payload for a specific vulnerability

        Args:
            vulnerability: Vulnerability details
            target: Target system
            context: Session context

        Returns:
            Dictionary with payload, delivery method, and precautions
        """
        self.logger.info(f"Creating exploit payload for: {vulnerability.get('title', 'unknown')}")

        prompt = f"""Create a safe exploitation payload for this vulnerability.

VULNERABILITY:
Title: {vulnerability.get('title')}
Description: {vulnerability.get('description')}
Severity: {vulnerability.get('severity')}
Target: {target}
Port: {vulnerability.get('port')}
Service: {vulnerability.get('service')}

CONTEXT:
{context[:1000]}

Requirements:
1. Generate a proof-of-concept exploit
2. Focus on verification, not destruction
3. Suggest safe payload that demonstrates vulnerability
4. Provide step-by-step exploitation process
5. Include detection/cleanup steps

Respond with ONLY valid JSON:
{{
  "payload": "The actual payload/exploit code",
  "delivery_method": "How to deliver the payload",
  "tool": "Tool to use (metasploit, sqlmap, manual, etc)",
  "command": "Command to execute the exploit",
  "expected_result": "What success looks like",
  "precautions": ["safety", "measures"],
  "cleanup": "How to clean up after testing"
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
            result = self._parse_json_response(content)

            self.logger.info(f"Created payload using: {result.get('tool', 'N/A')}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to create exploit payload: {e}", exc_info=True)
            return {
                "error": str(e),
                "payload": None
            }

    async def suggest_next_command(
        self,
        previous_command: str,
        previous_output: str,
        tool: str
    ) -> Dict[str, Any]:
        """
        Suggest follow-up command based on previous results

        Args:
            previous_command: Previously executed command
            previous_output: Output from previous command
            tool: Tool that was used

        Returns:
            Dictionary with suggested next command
        """
        self.logger.info(f"Suggesting follow-up command for {tool}")

        prompt = f"""Based on the previous command output, suggest an appropriate follow-up command.

PREVIOUS COMMAND: {previous_command}

OUTPUT:
{previous_output[:2000]}

TOOL: {tool}

Analyze the output and suggest:
1. What was discovered?
2. What is the logical next step?
3. What command should we run next?

Respond with ONLY valid JSON:
{{
  "discoveries": ["key", "findings", "from", "output"],
  "next_command": "suggested command",
  "reasoning": "why this command makes sense",
  "alternative_commands": ["other", "options"]
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
            result = self._parse_json_response(content)

            return result

        except Exception as e:
            self.logger.error(f"Failed to suggest next command: {e}", exc_info=True)
            return {}

    def _get_tool_specific_guidance(self, tool: str) -> str:
        """Get specific guidance for each tool"""
        guidance = {
            "nmap": """
- Use -sV for service version detection
- Use -sC for default scripts
- Consider -T4 for faster scanning (or -T2 for stealth)
- Use -p- for all ports or -p1-1000 for common ports
- Add -O for OS detection if needed
- Use -oX for XML output (easier parsing)
            """,
            "nikto": """
- Use -h for target host
- Consider -Tuning x for all tests
- Use -Format json for structured output
- Add -nossl if testing HTTP only
- Consider -maxtime to limit scan duration
            """,
            "sqlmap": """
- Use -u for target URL
- Add --batch for non-interactive mode
- Use --random-agent to avoid detection
- Consider --dbs to enumerate databases
- Add --tables and --dump for data extraction
- Use --level and --risk appropriately (start with 1,1)
            """,
            "gobuster": """
- Use dir mode for directory enumeration
- Specify wordlist with -w
- Set threads with -t (default 10, can increase to 50)
- Add -x for file extensions
- Use -q for quiet mode
- Consider -k to skip SSL verification
            """,
            "metasploit": """
- Use msfconsole -q for quiet mode
- Use 'use' to select module
- Set RHOST, RPORT, and other options
- Run 'check' before 'exploit' when possible
- Consider using auxiliary modules for verification
            """
        }
        return guidance.get(tool, "Generate appropriate command for this tool")

    def _get_fallback_command(self, tool: str, target: str) -> Dict[str, Any]:
        """Fallback commands if LLM fails"""
        fallback_commands = {
            "nmap": {
                "command": f"-sV -sC -T4 {target}",
                "full_command": f"nmap -sV -sC -T4 {target}",
                "explanation": "Basic service detection scan",
                "expected_output": "Open ports and service versions"
            },
            "nikto": {
                "command": f"-h {target}",
                "full_command": f"nikto -h {target}",
                "explanation": "Basic web vulnerability scan",
                "expected_output": "Web server vulnerabilities"
            },
            "sqlmap": {
                "command": f"-u http://{target} --batch",
                "full_command": f"sqlmap -u http://{target} --batch",
                "explanation": "Basic SQL injection test",
                "expected_output": "SQL injection vulnerabilities"
            },
            "gobuster": {
                "command": f"dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt",
                "full_command": f"gobuster dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt",
                "explanation": "Directory enumeration",
                "expected_output": "Hidden directories and files"
            }
        }

        return fallback_commands.get(tool, {
            "command": f"{target}",
            "full_command": f"{tool} {target}",
            "explanation": "Basic scan",
            "expected_output": "Unknown"
        })

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
            # Try to extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except:
                    pass
            return {}
