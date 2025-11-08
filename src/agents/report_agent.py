"""
Report Generation Agent
Automates Phase 6: Documentation and Comprehensive Report Generation

Generates professional penetration testing reports
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Report Generation Agent - Phase 6

    Responsibilities:
    - Generate comprehensive penetration test reports
    - Create executive summaries
    - Document all findings with evidence
    - Provide remediation recommendations
    - Export in multiple formats (HTML, JSON, PDF)
    """

    def __init__(self, orchestrator):
        """
        Initialize Report Generation Agent

        Args:
            orchestrator: Reference to main Orchestrator
        """
        self.orchestrator = orchestrator
        self.reasoning = orchestrator.reasoning
        self.generation = orchestrator.generation
        self.parsing = orchestrator.parsing
        self.logger = logger

    async def execute_phase(self, session_id: str) -> Dict[str, Any]:
        """
        Execute complete report generation phase

        Args:
            session_id: Penetration test session ID

        Returns:
            Phase execution results with report paths
        """
        self.logger.info(f"📋 Starting Report Generation Phase for session {session_id}")

        session = self.orchestrator.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        results = {
            'phase': 'reporting',
            'session_id': session_id,
            'target': session.target,
            'started_at': datetime.utcnow().isoformat(),
            'reports_generated': [],
            'report_paths': {}
        }

        try:
            # Step 1: Generate Executive Summary using LLM
            executive_summary = await self._generate_executive_summary(session)
            results['executive_summary'] = executive_summary

            # Step 2: Compile Technical Details
            technical_details = await self._compile_technical_details(session)
            results['technical_details'] = technical_details

            # Step 3: Generate Remediation Plan using LLM
            remediation_plan = await self._generate_remediation_plan(session)
            results['remediation_plan'] = remediation_plan

            # Step 4: Create JSON Report
            json_path = await self._generate_json_report(session, {
                'executive_summary': executive_summary,
                'technical_details': technical_details,
                'remediation_plan': remediation_plan
            })
            results['report_paths']['json'] = json_path
            results['reports_generated'].append('json')

            # Step 5: Create HTML Report
            html_path = await self._generate_html_report(session, {
                'executive_summary': executive_summary,
                'technical_details': technical_details,
                'remediation_plan': remediation_plan
            })
            results['report_paths']['html'] = html_path
            results['reports_generated'].append('html')

            # Step 6: Create Markdown Report
            md_path = await self._generate_markdown_report(session, {
                'executive_summary': executive_summary,
                'technical_details': technical_details,
                'remediation_plan': remediation_plan
            })
            results['report_paths']['markdown'] = md_path
            results['reports_generated'].append('markdown')

            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()

            self.logger.info(f"✅ Report generation completed: {len(results['reports_generated'])} formats")

        except Exception as e:
            self.logger.error(f"❌ Report generation phase failed: {e}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['completed_at'] = datetime.utcnow().isoformat()

        return results

    async def _generate_executive_summary(self, session) -> str:
        """
        Generate executive summary using LLM

        Args:
            session: Session object

        Returns:
            Executive summary text
        """
        self.logger.info("Generating executive summary with LLM")

        try:
            # Prepare session data for LLM
            session_data = {
                'target': session.target,
                'scope': session.scope,
                'duration': (datetime.utcnow() - session.started_at).total_seconds() / 3600,
                'total_vulnerabilities': len(session.vulnerabilities),
                'critical_count': len([v for v in session.vulnerabilities if v.severity.value == 'critical']),
                'high_count': len([v for v in session.vulnerabilities if v.severity.value == 'high']),
                'medium_count': len([v for v in session.vulnerabilities if v.severity.value == 'medium']),
                'low_count': len([v for v in session.vulnerabilities if v.severity.value == 'low'])
            }

            # Use reasoning module to generate summary
            summary = await self.reasoning.analyze_phase_results(
                phase='reporting',
                session_context=session_data,
                phase_results={'vulnerabilities': [v.model_dump() for v in session.vulnerabilities]},
                objective='Generate executive summary for C-level stakeholders (non-technical)'
            )

            return summary.get('executive_summary', 'Executive summary not available')

        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            return f"Penetration test completed on {session.target} with {len(session.vulnerabilities)} findings."

    async def _compile_technical_details(self, session) -> Dict[str, Any]:
        """
        Compile all technical details from the assessment

        Args:
            session: Session object

        Returns:
            Dictionary with technical details
        """
        self.logger.info("Compiling technical details")

        return {
            'target_information': {
                'target': session.target,
                'scope': session.scope,
                'authorized': session.authorized,
                'started_at': session.started_at.isoformat(),
                'completed_at': datetime.utcnow().isoformat()
            },
            'discovered_assets': getattr(session, 'discovered_assets', {}),
            'enumeration_data': getattr(session, 'enumeration_data', {}),
            'vulnerabilities': [v.model_dump() for v in session.vulnerabilities],
            'successful_exploits': getattr(session, 'successful_exploits', []),
            'tools_used': list(self.orchestrator.tools.keys()),
            'phases_completed': [
                'reconnaissance',
                'enumeration',
                'vulnerability_scanning',
                'exploitation',
                'post_exploitation',
                'reporting'
            ]
        }

    async def _generate_remediation_plan(self, session) -> List[Dict[str, Any]]:
        """
        Generate prioritized remediation plan using LLM

        Args:
            session: Session object

        Returns:
            List of remediation recommendations
        """
        self.logger.info("Generating remediation plan with LLM")

        try:
            # Get all vulnerabilities
            vulnerabilities = session.vulnerabilities

            # Use reasoning module to prioritize and plan
            plan = await self.reasoning.analyze_phase_results(
                phase='remediation_planning',
                session_context={'target': session.target},
                phase_results={'vulnerabilities': [v.model_dump() for v in vulnerabilities]},
                objective='Create prioritized remediation plan with timelines'
            )

            return plan.get('remediation_steps', [])

        except Exception as e:
            self.logger.error(f"Remediation plan generation failed: {e}")
            # Fallback: Use vulnerability remediation fields
            return [
                {
                    'priority': i + 1,
                    'vulnerability': v.title,
                    'severity': v.severity.value,
                    'remediation': v.remediation
                }
                for i, v in enumerate(sorted(
                    session.vulnerabilities,
                    key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.severity.value, 4)
                ))
            ]

    async def _generate_json_report(
        self,
        session,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Generate JSON report

        Args:
            session: Session object
            report_data: Report content

        Returns:
            Path to JSON report
        """
        self.logger.info("Generating JSON report")

        try:
            # Prepare report structure
            report = {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'report_type': 'penetration_test',
                    'format': 'json',
                    'version': '1.0'
                },
                'assessment_details': {
                    'target': session.target,
                    'scope': session.scope,
                    'session_id': session.session_id,
                    'started_at': session.started_at.isoformat(),
                    'completed_at': datetime.utcnow().isoformat()
                },
                'executive_summary': report_data['executive_summary'],
                'technical_findings': report_data['technical_details'],
                'remediation_plan': report_data['remediation_plan'],
                'statistics': {
                    'total_vulnerabilities': len(session.vulnerabilities),
                    'by_severity': {
                        'critical': len([v for v in session.vulnerabilities if v.severity.value == 'critical']),
                        'high': len([v for v in session.vulnerabilities if v.severity.value == 'high']),
                        'medium': len([v for v in session.vulnerabilities if v.severity.value == 'medium']),
                        'low': len([v for v in session.vulnerabilities if v.severity.value == 'low']),
                        'informational': len([v for v in session.vulnerabilities if v.severity.value == 'informational'])
                    }
                }
            }

            # Save to file
            reports_dir = Path('data/reports')
            reports_dir.mkdir(parents=True, exist_ok=True)

            filename = f"pentest_report_{session.session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = reports_dir / filename

            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.info(f"JSON report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"JSON report generation failed: {e}")
            raise

    async def _generate_html_report(
        self,
        session,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Generate HTML report

        Args:
            session: Session object
            report_data: Report content

        Returns:
            Path to HTML report
        """
        self.logger.info("Generating HTML report")

        try:
            # Generate HTML content
            html_content = self._create_html_report_content(session, report_data)

            # Save to file
            reports_dir = Path('data/reports')
            reports_dir.mkdir(parents=True, exist_ok=True)

            filename = f"pentest_report_{session.session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = reports_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"HTML report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"HTML report generation failed: {e}")
            raise

    async def _generate_markdown_report(
        self,
        session,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Generate Markdown report

        Args:
            session: Session object
            report_data: Report content

        Returns:
            Path to Markdown report
        """
        self.logger.info("Generating Markdown report")

        try:
            # Generate Markdown content
            md_content = self._create_markdown_report_content(session, report_data)

            # Save to file
            reports_dir = Path('data/reports')
            reports_dir.mkdir(parents=True, exist_ok=True)

            filename = f"pentest_report_{session.session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = reports_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

            self.logger.info(f"Markdown report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Markdown report generation failed: {e}")
            raise

    def _create_html_report_content(
        self,
        session,
        report_data: Dict[str, Any]
    ) -> str:
        """Create HTML report content"""

        vulnerabilities = session.vulnerabilities
        critical = [v for v in vulnerabilities if v.severity.value == 'critical']
        high = [v for v in vulnerabilities if v.severity.value == 'high']
        medium = [v for v in vulnerabilities if v.severity.value == 'medium']
        low = [v for v in vulnerabilities if v.severity.value == 'low']

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Penetration Test Report - {session.target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #0066cc; margin-top: 30px; }}
        h3 {{ color: #333; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .severity-critical {{ color: #fff; background: #d32f2f; padding: 3px 8px; border-radius: 3px; }}
        .severity-high {{ color: #fff; background: #f57c00; padding: 3px 8px; border-radius: 3px; }}
        .severity-medium {{ color: #fff; background: #fbc02d; padding: 3px 8px; border-radius: 3px; }}
        .severity-low {{ color: #fff; background: #388e3c; padding: 3px 8px; border-radius: 3px; }}
        .vuln-box {{ border-left: 4px solid #0066cc; padding: 15px; margin: 15px 0; background: #f9f9f9; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; padding: 15px; text-align: center; border-radius: 5px; background: #f4f4f4; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #0066cc; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Penetration Test Report</h1>
        <p><strong>Target:</strong> {session.target}</p>
        <p><strong>Session ID:</strong> {session.session_id}</p>
        <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
        <p><strong>Scope:</strong> {', '.join(session.scope)}</p>
    </div>

    <h2>Executive Summary</h2>
    <p>{report_data['executive_summary']}</p>

    <h2>Statistics</h2>
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{len(vulnerabilities)}</div>
            <div>Total Findings</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #d32f2f;">{len(critical)}</div>
            <div>Critical</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #f57c00;">{len(high)}</div>
            <div>High</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #fbc02d;">{len(medium)}</div>
            <div>Medium</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #388e3c;">{len(low)}</div>
            <div>Low</div>
        </div>
    </div>

    <h2>Vulnerabilities</h2>
"""

        # Add vulnerabilities
        for severity_name, severity_list in [('Critical', critical), ('High', high), ('Medium', medium), ('Low', low)]:
            if severity_list:
                html += f"<h3>{severity_name} Severity</h3>\n"
                for vuln in severity_list:
                    html += f"""
    <div class="vuln-box">
        <h4>{vuln.title} <span class="severity-{vuln.severity.value}">{vuln.severity.value.upper()}</span></h4>
        <p><strong>Description:</strong> {vuln.description}</p>
        <p><strong>Affected Component:</strong> {vuln.affected_component}</p>
        <p><strong>CVSS Score:</strong> {vuln.cvss_score}</p>
        {f'<p><strong>CVE ID:</strong> {vuln.cve_id}</p>' if vuln.cve_id else ''}
        <p><strong>Remediation:</strong> {vuln.remediation}</p>
    </div>
"""

        html += """
    <h2>Remediation Plan</h2>
    <table>
        <tr>
            <th>Priority</th>
            <th>Vulnerability</th>
            <th>Severity</th>
            <th>Remediation</th>
        </tr>
"""

        for item in report_data['remediation_plan'][:10]:  # Top 10
            html += f"""
        <tr>
            <td>{item.get('priority', 'N/A')}</td>
            <td>{item.get('vulnerability', 'N/A')}</td>
            <td><span class="severity-{item.get('severity', 'low')}">{item.get('severity', 'N/A').upper()}</span></td>
            <td>{item.get('remediation', 'N/A')}</td>
        </tr>
"""

        html += """
    </table>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 2px solid #ddd; color: #666;">
        <p>Report generated by EHPA (Ethical Hacking Personal Assistant)</p>
        <p>Generated at: {datetime.utcnow().isoformat()}</p>
    </footer>
</body>
</html>
"""
        return html

    def _create_markdown_report_content(
        self,
        session,
        report_data: Dict[str, Any]
    ) -> str:
        """Create Markdown report content"""

        vulnerabilities = session.vulnerabilities

        md = f"""# Penetration Test Report

## Assessment Details

- **Target:** {session.target}
- **Session ID:** {session.session_id}
- **Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
- **Scope:** {', '.join(session.scope)}

## Executive Summary

{report_data['executive_summary']}

## Statistics

| Metric | Count |
|--------|-------|
| Total Vulnerabilities | {len(vulnerabilities)} |
| Critical | {len([v for v in vulnerabilities if v.severity.value == 'critical'])} |
| High | {len([v for v in vulnerabilities if v.severity.value == 'high'])} |
| Medium | {len([v for v in vulnerabilities if v.severity.value == 'medium'])} |
| Low | {len([v for v in vulnerabilities if v.severity.value == 'low'])} |

## Vulnerabilities

"""

        # Add vulnerabilities
        for vuln in vulnerabilities:
            md += f"""
### {vuln.title}

**Severity:** {vuln.severity.value.upper()}
**CVSS Score:** {vuln.cvss_score}
**Affected Component:** {vuln.affected_component}
{f'**CVE ID:** {vuln.cve_id}  ' if vuln.cve_id else ''}

**Description:**
{vuln.description}

**Remediation:**
{vuln.remediation}

---

"""

        md += f"""
## Remediation Plan

| Priority | Vulnerability | Severity | Remediation |
|----------|---------------|----------|-------------|
"""

        for item in report_data['remediation_plan'][:10]:
            md += f"| {item.get('priority', 'N/A')} | {item.get('vulnerability', 'N/A')} | {item.get('severity', 'N/A').upper()} | {item.get('remediation', 'N/A')} |\n"

        md += f"""

---

*Report generated by EHPA (Ethical Hacking Personal Assistant)*
*Generated at: {datetime.utcnow().isoformat()}*
"""

        return md
