#!/usr/bin/env python3
"""
Quick setup verification script
Checks if the EHPA system is configured correctly
"""

import os
import sys
from pathlib import Path

def check_item(name, condition, details=""):
    """Print check result"""
    status = "OK" if condition else "FAIL"
    symbol = "[+]" if condition else "[X]"
    print(f"{symbol} {name}: {status}")
    if details and not condition:
        print(f"    -> {details}")
    return condition

def main():
    print("="*60)
    print("EHPA Task 1 - Setup Verification")
    print("="*60)
    print()

    all_checks = []

    # Check 1: Python version
    print("[1] Python Version Check")
    python_version = sys.version_info
    is_python_ok = python_version >= (3, 9)
    all_checks.append(check_item(
        "Python 3.9+",
        is_python_ok,
        f"Found Python {python_version.major}.{python_version.minor}, need 3.9+"
    ))
    print()

    # Check 2: .env file exists
    print("[2] Configuration Files")
    env_file = Path(".env")
    all_checks.append(check_item(
        ".env file exists",
        env_file.exists(),
        "Run: cp .env.template .env"
    ))

    gitignore_file = Path(".gitignore")
    all_checks.append(check_item(
        ".gitignore exists",
        gitignore_file.exists(),
        "Security risk: .env might be committed to Git"
    ))
    print()

    # Check 3: API Key
    print("[3] API Key Configuration")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

        has_key = bool(api_key)
        all_checks.append(check_item(
            "API key loaded",
            has_key,
            "Add ANTHROPIC_API_KEY to .env file"
        ))

        if has_key:
            is_valid_format = api_key.startswith('sk-ant-')
            all_checks.append(check_item(
                "API key format valid",
                is_valid_format,
                "Key should start with 'sk-ant-'"
            ))

            is_not_placeholder = api_key != "your_api_key_here"
            all_checks.append(check_item(
                "API key is not placeholder",
                is_not_placeholder,
                "Replace 'your_api_key_here' with actual key"
            ))
    except ImportError:
        all_checks.append(check_item(
            "python-dotenv installed",
            False,
            "Run: pip install python-dotenv"
        ))
    print()

    # Check 4: Required directories
    print("[4] Directory Structure")
    required_dirs = ['data', 'logs', 'config', 'src']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        all_checks.append(check_item(
            f"{dir_name}/ directory",
            dir_path.exists()
        ))
    print()

    # Check 5: Key dependencies
    print("[5] Python Dependencies")
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('anthropic', 'Anthropic SDK'),
        ('pydantic', 'Pydantic'),
        ('uvicorn', 'Uvicorn'),
    ]

    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            all_checks.append(check_item(f"{display_name}", True))
        except ImportError:
            all_checks.append(check_item(
                f"{display_name}",
                False,
                f"Run: pip install {module_name}"
            ))
    print()

    # Check 6: Test Anthropic connection
    print("[6] API Connection Test")
    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key and api_key != "your_api_key_here":
            try:
                client = Anthropic(api_key=api_key)
                # Simple test - just creating client is enough for now
                all_checks.append(check_item(
                    "Anthropic client created",
                    True
                ))
            except Exception as e:
                all_checks.append(check_item(
                    "Anthropic client created",
                    False,
                    f"Error: {str(e)}"
                ))
        else:
            all_checks.append(check_item(
                "Anthropic client created",
                False,
                "No valid API key found"
            ))
    except ImportError:
        all_checks.append(check_item(
            "Anthropic SDK available",
            False,
            "Run: pip install anthropic"
        ))
    print()

    # Summary
    print("="*60)
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"SUMMARY: {passed}/{total} checks passed ({percentage:.1f}%)")
    print("="*60)
    print()

    if passed == total:
        print("✓ All checks passed! Your system is ready.")
        print()
        print("Next steps:")
        print("  1. Run: python main.py")
        print("  2. Open: http://localhost:8000/api/docs")
        print("  3. Start your first pentest!")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Add API key to .env file")
        print("  - Create missing directories")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
