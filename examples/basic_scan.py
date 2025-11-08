#!/usr/bin/env python3
"""
EHPA Basic Scan Example
Demonstrates a simple network scan using EHPA orchestrator
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import Orchestrator
from src.core.config import config


async def main():
    """
    Run a basic network scan on a target
    """
    print("="*70)
    print("  EHPA - Basic Scan Example")
    print("="*70)

    # Initialize orchestrator
    print("\n📋 Initializing orchestrator...")
    orchestrator = Orchestrator()

    # Target configuration
    target = "scanme.nmap.org"  # Safe, authorized test target
    scope = ["network"]  # Only network scanning

    print(f"\n🎯 Target: {target}")
    print(f"📍 Scope: {', '.join(scope)}")

    try:
        # Start penetration test session
        print("\n🚀 Starting penetration test session...")
        session = await orchestrator.start_pentest(
            target=target,
            scope=scope,
            authorized=True
        )

        print(f"✅ Session created: {session.session_id}")
        print(f"📊 Current phase: {session.current_phase.value}")
        print(f"📝 Initial tasks: {len(session.todo_list)}")

        # Execute workflow (limit to reconnaissance phase only for demo)
        print("\n⚙️  Executing reconnaissance phase...")
        print("   This will:")
        print("   - Scan for open ports (nmap)")
        print("   - Identify services")
        print("   - Detect technologies")

        # Run limited workflow (max 10 iterations for demo)
        await orchestrator.execute_workflow(
            session.session_id,
            max_iterations=10
        )

        # Get results
        print("\n" + "="*70)
        print("📊 SCAN RESULTS")
        print("="*70)

        print(f"\nPhase: {session.current_phase.value}")
        print(f"Progress: {session.progress:.1f}%")
        print(f"Tasks completed: {len(session.completed_tasks)}")

        # Display target information
        if session.target_info.ip_addresses:
            print(f"\n🌐 IP Addresses:")
            for ip in session.target_info.ip_addresses:
                print(f"   - {ip}")

        if session.target_info.open_ports:
            print(f"\n🔓 Open Ports: {len(session.target_info.open_ports)}")
            for port in sorted(session.target_info.open_ports)[:10]:
                service = session.target_info.services.get(port, "unknown")
                print(f"   - {port}/tcp  {service}")
            if len(session.target_info.open_ports) > 10:
                print(f"   ... and {len(session.target_info.open_ports) - 10} more")

        if session.target_info.technologies:
            print(f"\n⚙️  Technologies Detected:")
            for tech in session.target_info.technologies:
                print(f"   - {tech}")

        # Display vulnerabilities found
        if session.vulnerabilities:
            print(f"\n🔍 Vulnerabilities Found: {len(session.vulnerabilities)}")
            for vuln in session.vulnerabilities[:5]:
                print(f"\n   [{vuln.severity.value.upper()}] {vuln.title}")
                print(f"   → {vuln.description}")
            if len(session.vulnerabilities) > 5:
                print(f"\n   ... and {len(session.vulnerabilities) - 5} more")
        else:
            print("\n✅ No vulnerabilities found")

        # Display findings
        if session.findings:
            print(f"\n📋 General Findings: {len(session.findings)}")
            for finding in session.findings[:3]:
                print(f"   - {finding.title}")
            if len(session.findings) > 3:
                print(f"   ... and {len(session.findings) - 3} more")

        print("\n" + "="*70)
        print(f"✅ Scan complete! Session ID: {session.session_id}")
        print(f"📁 Session saved to: data/sessions/{session.session_id}.json")
        print("="*70)

        # Generate report
        print("\n📄 Generating report...")
        report_path = await orchestrator.generate_report(session.session_id)
        print(f"✅ Report generated: {report_path}")

    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        await orchestrator.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
