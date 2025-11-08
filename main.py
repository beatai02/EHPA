#!/usr/bin/env python3
"""
EHPA Task 1 - Backend Orchestration System
Main Entry Point

Starts the FastAPI server that exposes the penetration testing orchestration API
"""

import sys
import uvicorn
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import config
from src.utils.logger import setup_logging, get_logger


def main():
    """Main entry point"""
    # Setup logging
    setup_logging(
        log_level=config.settings.log_level,
        log_format=config.settings.log_format,
        log_dir=Path(config.settings.logs_dir)
    )

    logger = get_logger(__name__)

    # Validate configuration
    is_valid, errors = config.validate_config()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.warning("Some features may not work correctly")

    # Print banner
    print("\n" + "="*70)
    print("  EHPA Task 1 - Backend Orchestration System")
    print("  LLM-Powered Penetration Testing Framework")
    print("="*70)
    print(f"  API Server: http://{config.api.host}:{config.api.port}")
    print(f"  API Docs: http://{config.api.host}:{config.api.port}/api/docs")
    print(f"  LLM Model: {config.llm.model}")
    print(f"  MCP Tools: nmap, nikto, sqlmap, gobuster")
    print("="*70 + "\n")

    logger.info("Starting EHPA Backend Orchestration System")
    logger.info(f"Configuration: {config.to_dict()}")

    # Run FastAPI server
    try:
        uvicorn.run(
            "src.api.server:app",
            host=config.api.host,
            port=config.api.port,
            workers=1,  # Single worker for development; increase for production
            log_level=config.settings.log_level.lower(),
            reload=False,  # Set to True for development
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
