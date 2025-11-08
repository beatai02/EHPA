"""
Base MCP Server
Abstract base class for all penetration testing tool servers
Provides standard interface and common functionality
"""

import asyncio
import subprocess
import logging
import shlex
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.config import config
from ..utils.logger import get_logger


class BaseMCPServer(ABC):
    """
    Base class for MCP tool servers

    Each tool server wraps a penetration testing tool and provides:
    - Standard interface for execution
    - Input validation
    - Output formatting
    - Error handling
    - Timeout management
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.logger = get_logger(f"mcp.{tool_name}")

        # Load tool configuration
        self.tool_config = config.get_tool_config(tool_name)
        self.binary_path = self.tool_config.get('binary_path', f'/usr/bin/{tool_name}')
        self.default_flags = self.tool_config.get('default_flags', [])
        self.max_timeout = self.tool_config.get('max_timeout', 300)
        self.output_format = self.tool_config.get('output_format', 'text')

        self.logger.info(f"{tool_name} MCP server initialized")

    @abstractmethod
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Return the MCP tool schema
        Defines the tool's interface, parameters, and capabilities
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters

        Returns:
            (is_valid, error_message)
        """
        pass

    @abstractmethod
    def build_command(self, params: Dict[str, Any]) -> str:
        """
        Build the command to execute from parameters

        Returns:
            Command string (without the binary path)
        """
        pass

    @abstractmethod
    async def parse_output(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse tool output into structured format

        Returns:
            Dictionary with parsed results
        """
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method
        Orchestrates validation, execution, and parsing

        Args:
            params: Tool parameters

        Returns:
            Dictionary with execution results
        """
        self.logger.info(f"Executing {self.tool_name} with params: {params}")

        # Validate parameters
        is_valid, error_msg = self.validate_params(params)
        if not is_valid:
            self.logger.error(f"Parameter validation failed: {error_msg}")
            return {
                'success': False,
                'error': f"Invalid parameters: {error_msg}",
                'tool': self.tool_name
            }

        # Check target authorization
        target = params.get('target', '')
        if target and not self._is_target_authorized(target):
            self.logger.error(f"Unauthorized target: {target}")
            return {
                'success': False,
                'error': f"Target {target} is not authorized for testing",
                'tool': self.tool_name
            }

        try:
            # Build command
            command_args = self.build_command(params)
            full_command = f"{self.binary_path} {command_args}"

            self.logger.info(f"Executing command: {full_command}")

            # Execute command
            output, error, return_code = await self._run_command(full_command)

            # Parse output
            if return_code == 0 or output:  # Some tools return non-zero on findings
                parsed_result = await self.parse_output(output, params)

                return {
                    'success': True,
                    'tool': self.tool_name,
                    'command': full_command,
                    'output': output,
                    'error_output': error if error else None,
                    'return_code': return_code,
                    'parsed': parsed_result
                }
            else:
                self.logger.error(f"Command failed with code {return_code}: {error}")
                return {
                    'success': False,
                    'tool': self.tool_name,
                    'command': full_command,
                    'error': error,
                    'return_code': return_code
                }

        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout after {self.max_timeout} seconds")
            return {
                'success': False,
                'tool': self.tool_name,
                'error': f"Command timeout after {self.max_timeout} seconds"
            }
        except Exception as e:
            self.logger.error(f"Execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'tool': self.tool_name,
                'error': str(e)
            }

    async def _run_command(self, command: str) -> tuple[str, str, int]:
        """
        Run shell command asynchronously with timeout

        Returns:
            (stdout, stderr, return_code)
        """
        try:
            # Split command safely
            # Note: For production, use proper argument passing
            # For now, we'll use shell=True for flexibility with tool arguments

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024 * 10  # 10MB buffer limit
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.max_timeout
            )

            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')

            return stdout_text, stderr_text, process.returncode

        except asyncio.TimeoutError:
            # Kill the process
            try:
                process.kill()
                await process.wait()
            except:
                pass
            raise

    def _is_target_authorized(self, target: str) -> bool:
        """Check if target is authorized for testing"""
        # In production, implement proper authorization checking
        # For now, use config's authorization check
        if not config.security.require_target_approval:
            return True

        return config.is_target_allowed(target)

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command to prevent injection"""
        # Basic sanitization - in production, use more robust methods
        dangerous_chars = [';', '&&', '||', '|', '`', '$', '(', ')']
        for char in dangerous_chars:
            if char in command:
                self.logger.warning(f"Potentially dangerous character in command: {char}")

        return command

    def _save_output(self, output: str, task_id: Optional[str] = None) -> Path:
        """Save raw output to file"""
        output_dir = Path(config.settings.data_dir) / 'tool_outputs' / self.tool_name
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{task_id or 'output'}_{self.tool_name}.txt"
        output_path = output_dir / filename

        with open(output_path, 'w') as f:
            f.write(output)

        self.logger.debug(f"Saved output to: {output_path}")
        return output_path

    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            'tool_name': self.tool_name,
            'binary_path': self.binary_path,
            'default_flags': self.default_flags,
            'max_timeout': self.max_timeout,
            'output_format': self.output_format,
            'schema': self.get_tool_schema()
        }
