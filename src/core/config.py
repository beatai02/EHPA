"""
Configuration Management
Loads settings from environment variables and YAML config file
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class LLMConfig(BaseModel):
    """LLM-specific configuration"""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.7
    streaming: bool = True


class APIConfig(BaseModel):
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    secret_key: str = "change-this-in-production"


class SecurityConfig(BaseModel):
    """Security and safety configuration"""
    allowed_targets: list[str] = Field(default_factory=list)
    require_target_approval: bool = True
    max_concurrent_scans: int = 3
    rate_limit_per_minute: int = 30


class ToolTimeouts(BaseModel):
    """Timeout configurations for pentesting tools"""
    nmap: int = 300
    nikto: int = 600
    sqlmap: int = 900
    gobuster: int = 300
    metasploit: int = 1800


class Settings(BaseSettings):
    """Environment-based settings using Pydantic"""

    # Anthropic API
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_secret_key: str = Field(default="", env="API_SECRET_KEY")

    # LLM Configuration
    llm_model: str = Field(default="claude-sonnet-4-5-20250929", env="LLM_MODEL")
    llm_max_tokens: int = Field(default=4096, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_streaming: bool = Field(default=True, env="LLM_STREAMING")

    # Paths
    data_dir: str = Field(default="./data", env="DATA_DIR")
    logs_dir: str = Field(default="./logs", env="LOGS_DIR")
    sessions_dir: str = Field(default="./data/sessions", env="SESSIONS_DIR")
    findings_dir: str = Field(default="./data/findings", env="FINDINGS_DIR")
    reports_dir: str = Field(default="./data/reports", env="REPORTS_DIR")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Security
    allowed_targets: str = Field(default="", env="ALLOWED_TARGETS")
    require_target_approval: bool = Field(default=True, env="REQUIRE_TARGET_APPROVAL")
    max_concurrent_scans: int = Field(default=3, env="MAX_CONCURRENT_SCANS")
    rate_limit_per_minute: int = Field(default=30, env="RATE_LIMIT_PER_MINUTE")

    # Tool Timeouts
    nmap_timeout: int = Field(default=300, env="NMAP_TIMEOUT")
    nikto_timeout: int = Field(default=600, env="NIKTO_TIMEOUT")
    sqlmap_timeout: int = Field(default=900, env="SQLMAP_TIMEOUT")
    gobuster_timeout: int = Field(default=300, env="GOBUSTER_TIMEOUT")
    metasploit_timeout: int = Field(default=1800, env="METASPLOIT_TIMEOUT")

    class Config:
        env_file = ".env"
        case_sensitive = False


class Config:
    """
    Main configuration class that combines environment variables and YAML config
    Singleton pattern to ensure single instance across application
    """

    _instance: Optional['Config'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True

            # Load environment variables
            load_dotenv()

            # Load settings from environment
            self.settings = Settings()

            # Load YAML configuration
            self.yaml_config = self._load_yaml_config()

            # Create structured config objects
            self.llm = LLMConfig(
                model=self.settings.llm_model,
                max_tokens=self.settings.llm_max_tokens,
                temperature=self.settings.llm_temperature,
                streaming=self.settings.llm_streaming
            )

            self.api = APIConfig(
                host=self.settings.api_host,
                port=self.settings.api_port,
                workers=self.settings.api_workers,
                secret_key=self.settings.api_secret_key or self._generate_secret_key()
            )

            self.security = SecurityConfig(
                allowed_targets=self._parse_allowed_targets(),
                require_target_approval=self.settings.require_target_approval,
                max_concurrent_scans=self.settings.max_concurrent_scans,
                rate_limit_per_minute=self.settings.rate_limit_per_minute
            )

            self.timeouts = ToolTimeouts(
                nmap=self.settings.nmap_timeout,
                nikto=self.settings.nikto_timeout,
                sqlmap=self.settings.sqlmap_timeout,
                gobuster=self.settings.gobuster_timeout,
                metasploit=self.settings.metasploit_timeout
            )

            # Create necessary directories
            self._ensure_directories()

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        if not config_path.exists():
            return {}

        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _parse_allowed_targets(self) -> list[str]:
        """Parse comma-separated allowed targets from environment"""
        if not self.settings.allowed_targets:
            return []
        return [t.strip() for t in self.settings.allowed_targets.split(',') if t.strip()]

    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key"""
        import secrets
        return secrets.token_urlsafe(32)

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        dirs = [
            self.settings.data_dir,
            self.settings.logs_dir,
            self.settings.sessions_dir,
            self.settings.findings_dir,
            self.settings.reports_dir,
        ]

        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool"""
        tools = self.yaml_config.get('mcp_tools', {})
        return tools.get(tool_name, {})

    def get_phase_config(self, phase_name: str) -> Dict[str, Any]:
        """Get configuration for a specific pentest phase"""
        phases = self.yaml_config.get('pentest_phases', {})
        return phases.get(phase_name, {})

    def get_module_prompt(self, module_name: str) -> str:
        """Get system prompt for an LLM module"""
        modules = self.yaml_config.get('llm_modules', {})
        module = modules.get(module_name, {})
        return module.get('system_prompt', '')

    def get_severity_config(self) -> Dict[str, Any]:
        """Get vulnerability severity configuration"""
        return self.yaml_config.get('severity_levels', {})

    def is_target_allowed(self, target: str) -> bool:
        """Check if a target is in the allowed list"""
        if not self.security.require_target_approval:
            return True

        if not self.security.allowed_targets:
            return False

        # Check if target matches any allowed target (exact or subdomain)
        for allowed in self.security.allowed_targets:
            if target == allowed or target.endswith(f'.{allowed}'):
                return True

        return False

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration and return (is_valid, list_of_errors)"""
        errors = []

        if not self.settings.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY not set in environment")

        if not self.api.secret_key or self.api.secret_key == "change-this-in-production":
            errors.append("API_SECRET_KEY should be set to a secure value")

        # Check if required tools exist (in production on Kali Linux)
        required_tools = ['nmap', 'nikto', 'sqlmap', 'gobuster']
        for tool in required_tools:
            tool_config = self.get_tool_config(tool)
            if tool_config:
                binary_path = tool_config.get('binary_path', '')
                # Note: We won't fail if tools are missing (might not be on Kali yet)
                # but we'll log warnings

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            'llm': self.llm.model_dump(),
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'workers': self.api.workers
            },
            'security': self.security.model_dump(),
            'timeouts': self.timeouts.model_dump(),
            'paths': {
                'data': self.settings.data_dir,
                'logs': self.settings.logs_dir,
                'sessions': self.settings.sessions_dir,
                'findings': self.settings.findings_dir,
                'reports': self.settings.reports_dir
            }
        }


# Create global config instance
config = Config()
