"""
EHPA (Ethical Hacking Personal Assistant) Setup Configuration
Installation script for Python package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README_SIMPLE.md").read_text(encoding='utf-8')

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()
requirements = [r.strip() for r in requirements if r.strip() and not r.startswith('#')]

setup(
    name="ehpa",
    version="1.0.0",
    author="EHPA Team",
    author_email="ehpa@example.com",
    description="AI-Powered Ethical Hacking Personal Assistant - LLM-based penetration testing orchestration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ehpa-task1",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
        ],
        "hexstrike": [
            "hexstrike-mcp-client>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ehpa=src.main:main",
            "ehpa-server=src.api.server:app",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "configs/*.yaml",
            "web/templates/*.html",
            "web/static/css/*.css",
            "web/static/js/*.js",
        ],
    },
    keywords=[
        "pentesting",
        "security",
        "ethical-hacking",
        "llm",
        "ai",
        "claude",
        "anthropic",
        "automation",
        "orchestration",
        "vulnerability-scanner",
        "network-security",
        "web-security",
        "mcp",
        "hexstrike",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ehpa-task1/issues",
        "Documentation": "https://github.com/yourusername/ehpa-task1/blob/main/README_SIMPLE.md",
        "Source": "https://github.com/yourusername/ehpa-task1",
    },
    zip_safe=False,
)
