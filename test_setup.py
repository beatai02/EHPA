#!/usr/bin/env python3
"""
Quick Setup Test Script
Verifies that all components are properly installed and configured
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")

    try:
        # Core dependencies
        import anthropic
        print("  ✅ anthropic")

        import fastapi
        print("  ✅ fastapi")

        import uvicorn
        print("  ✅ uvicorn")

        import pydantic
        print("  ✅ pydantic")

        # Internal modules
        from src.core.config import config
        print("  ✅ src.core.config")

        from src.core.session import Session
        print("  ✅ src.core.session")

        from src.core.orchestrator import Orchestrator
        print("  ✅ src.core.orchestrator")

        from src.modules.reasoning import ReasoningModule
        print("  ✅ src.modules.reasoning")

        from src.modules.generation import GenerationModule
        print("  ✅ src.modules.generation")

        from src.modules.parsing import ParsingModule
        print("  ✅ src.modules.parsing")

        from src.mcp.nmap_server import NmapMCPServer
        print("  ✅ src.mcp.nmap_server")

        from src.api.server import app
        print("  ✅ src.api.server")

        return True

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")

    try:
        from src.core.config import config

        # Check critical settings
        if not config.settings.anthropic_api_key:
            print("  ⚠️  WARNING: ANTHROPIC_API_KEY not set")
        else:
            # Mask the key
            masked_key = config.settings.anthropic_api_key[:10] + "..." + config.settings.anthropic_api_key[-4:]
            print(f"  ✅ API Key configured: {masked_key}")

        print(f"  ✅ LLM Model: {config.llm.model}")
        print(f"  ✅ API Host: {config.api.host}:{config.api.port}")
        print(f"  ✅ Log Level: {config.settings.log_level}")

        # Validate config
        is_valid, errors = config.validate_config()
        if not is_valid:
            print("  ⚠️  Configuration warnings:")
            for error in errors:
                print(f"     - {error}")
        else:
            print("  ✅ Configuration valid")

        return True

    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_directories():
    """Test that required directories exist"""
    print("\n📁 Testing directories...")

    required_dirs = [
        "data/sessions",
        "data/findings",
        "data/reports",
        "logs"
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (missing)")
            all_exist = False

    return all_exist


def test_mcp_tools():
    """Test MCP tool servers"""
    print("\n🔨 Testing MCP tool servers...")

    try:
        from src.mcp.nmap_server import NmapMCPServer
        from src.mcp.nikto_server import NiktoMCPServer
        from src.mcp.sqlmap_server import SQLMapMCPServer
        from src.mcp.gobuster_server import GobusterMCPServer

        tools = {
            'nmap': NmapMCPServer(),
            'nikto': NiktoMCPServer(),
            'sqlmap': SQLMapMCPServer(),
            'gobuster': GobusterMCPServer()
        }

        for name, tool in tools.items():
            schema = tool.get_tool_schema()
            print(f"  ✅ {name}: {schema['description']}")

        return True

    except Exception as e:
        print(f"  ❌ MCP tool error: {e}")
        return False


def test_llm_modules():
    """Test LLM modules initialization"""
    print("\n🧠 Testing LLM modules...")

    try:
        from src.modules.reasoning import ReasoningModule
        from src.modules.generation import GenerationModule
        from src.modules.parsing import ParsingModule

        reasoning = ReasoningModule()
        print(f"  ✅ Reasoning Module (model: {reasoning.model})")

        generation = GenerationModule()
        print(f"  ✅ Generation Module (model: {generation.model})")

        parsing = ParsingModule()
        print(f"  ✅ Parsing Module (model: {parsing.model})")

        return True

    except Exception as e:
        print(f"  ❌ LLM module error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("  EHPA Task 1 - Setup Verification")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("Directories", test_directories()))
    results.append(("MCP Tools", test_mcp_tools()))
    results.append(("LLM Modules", test_llm_modules()))

    # Summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✅ All tests passed! System is ready.")
        print("\nYou can now start the server:")
        print("  python3 main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
