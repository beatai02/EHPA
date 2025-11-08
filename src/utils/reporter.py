"""
Report Generation Utility
Generates comprehensive penetration test reports
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Template

from ..core.session import Session, SeverityLevel
from ..core.config import config
from .logger import get_logger

logger = get_logger(__name__)


# HTML Report Template
HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Penetration Test Report - {{ session.target }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .meta-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .meta-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .meta-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .meta-card p {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }
        .content {
            padding: 40px;
        }
        section {
            margin-bottom: 40px;
        }
        h2 {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h3 {
            color: #764ba2;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .executive-summary {
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #667eea;
            margin-bottom: 30px;
        }
        .severity-critical {
            color: #dc3545;
            font-weight: bold;
        }
        .severity-high {
            color: #fd7e14;
            font-weight: bold;
        }
        .severity-medium {
            color: #ffc107;
            font-weight: bold;
        }
        .severity-low {
            color: #17a2b8;
            font-weight: bold;
        }
        .severity-info {
            color: #6c757d;
            font-weight: bold;
        }
        .vulnerability {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .vulnerability-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .vulnerability-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }
        .vulnerability-details {
            margin-top: 15px;
        }
        .detail-row {
            margin: 8px 0;
            display: grid;
            grid-template-columns: 150px 1fr;
        }
        .detail-label {
            font-weight: bold;
            color: #666;
        }
        .evidence {
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .remediation {
            background: #d4edda;
            border-left: 3px solid #28a745;
            padding: 15px;
            margin-top: 15px;
        }
        .statistics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        footer {
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #667eea;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Penetration Test Report</h1>
            <p>Target: {{ session.target }}</p>
            <p>{{ generated_at }}</p>
        </header>

        <div class="meta-info">
            <div class="meta-card">
                <h3>Session ID</h3>
                <p style="font-size: 1em;">{{ session.session_id }}</p>
            </div>
            <div class="meta-card">
                <h3>Duration</h3>
                <p>{{ duration }}</p>
            </div>
            <div class="meta-card">
                <h3>Scope</h3>
                <p style="font-size: 1em;">{{ scope }}</p>
            </div>
            <div class="meta-card">
                <h3>Status</h3>
                <p style="font-size: 1em;">{{ session.status|upper }}</p>
            </div>
        </div>

        <div class="content">
            {% if analysis %}
            <section class="executive-summary">
                <h2>Executive Summary</h2>
                <p><strong>Overall Risk Level:</strong> <span class="severity-{{ analysis.overall_risk }}">{{ analysis.overall_risk|upper }}</span></p>
                <p style="margin-top: 15px;">{{ analysis.executive_summary }}</p>
            </section>
            {% endif %}

            <section>
                <h2>Findings Summary</h2>
                <div class="statistics">
                    <div class="stat-card">
                        <div class="stat-number">{{ vulnerabilities|length }}</div>
                        <div class="stat-label">Total Vulnerabilities</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ critical_count }}</div>
                        <div class="stat-label">Critical</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ high_count }}</div>
                        <div class="stat-label">High</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ medium_count }}</div>
                        <div class="stat-label">Medium</div>
                    </div>
                </div>
            </section>

            {% if session.target_info %}
            <section>
                <h2>Target Information</h2>
                <table>
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>IP Addresses</td>
                        <td>{{ session.target_info.ip_addresses|join(', ') or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <td>Open Ports</td>
                        <td>{{ session.target_info.open_ports|join(', ') or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <td>Technologies</td>
                        <td>{{ session.target_info.technologies|join(', ') or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <td>Operating System</td>
                        <td>{{ session.target_info.operating_system or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <td>Web Server</td>
                        <td>{{ session.target_info.web_server or 'N/A' }}</td>
                    </tr>
                </table>
            </section>
            {% endif %}

            <section>
                <h2>Vulnerabilities</h2>
                {% if vulnerabilities %}
                    {% for vuln in vulnerabilities %}
                    <div class="vulnerability">
                        <div class="vulnerability-header">
                            <div class="vulnerability-title">{{ vuln.title }}</div>
                            <div class="severity-{{ vuln.severity }}">{{ vuln.severity|upper }}</div>
                        </div>
                        <p>{{ vuln.description }}</p>
                        <div class="vulnerability-details">
                            <div class="detail-row">
                                <span class="detail-label">Target:</span>
                                <span>{{ vuln.target }}</span>
                            </div>
                            {% if vuln.port %}
                            <div class="detail-row">
                                <span class="detail-label">Port:</span>
                                <span>{{ vuln.port }}</span>
                            </div>
                            {% endif %}
                            {% if vuln.service %}
                            <div class="detail-row">
                                <span class="detail-label">Service:</span>
                                <span>{{ vuln.service }}</span>
                            </div>
                            {% endif %}
                            {% if vuln.cvss_score %}
                            <div class="detail-row">
                                <span class="detail-label">CVSS Score:</span>
                                <span>{{ vuln.cvss_score }}</span>
                            </div>
                            {% endif %}
                            <div class="detail-row">
                                <span class="detail-label">Discovered By:</span>
                                <span>{{ vuln.discovered_by }}</span>
                            </div>
                        </div>
                        {% if vuln.evidence %}
                        <div class="evidence">
                            <strong>Evidence:</strong><br>
                            {{ vuln.evidence[:500] }}{% if vuln.evidence|length > 500 %}...{% endif %}
                        </div>
                        {% endif %}
                        {% if vuln.remediation %}
                        <div class="remediation">
                            <strong>Remediation:</strong><br>
                            {{ vuln.remediation }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No vulnerabilities discovered.</p>
                {% endif %}
            </section>

            {% if analysis and analysis.recommendations %}
            <section>
                <h2>Recommendations</h2>
                {% for rec in analysis.recommendations %}
                <div class="vulnerability">
                    <div class="vulnerability-header">
                        <div class="vulnerability-title">{{ rec.action }}</div>
                        <div class="severity-{{ rec.priority }}">{{ rec.priority|upper }} PRIORITY</div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Effort:</span>
                        <span>{{ rec.effort|upper }}</span>
                    </div>
                </div>
                {% endfor %}
            </section>
            {% endif %}

            <section>
                <h2>Testing Methodology</h2>
                <p>This penetration test followed the PTES (Penetration Testing Execution Standard) methodology:</p>
                <ol style="margin-left: 20px; margin-top: 15px;">
                    <li><strong>Reconnaissance:</strong> Information gathering and target discovery</li>
                    <li><strong>Scanning:</strong> Vulnerability identification and service enumeration</li>
                    <li><strong>Exploitation:</strong> Vulnerability validation and exploitation attempts</li>
                    <li><strong>Reporting:</strong> Documentation of findings and recommendations</li>
                </ol>
            </section>

            <section>
                <h2>Tasks Executed</h2>
                <p><strong>Total Tasks:</strong> {{ session.completed_tasks|length }}</p>
                <table>
                    <tr>
                        <th>Description</th>
                        <th>Tool</th>
                        <th>Findings</th>
                    </tr>
                    {% for task in session.completed_tasks[-20:] %}
                    <tr>
                        <td>{{ task.description }}</td>
                        <td>{{ task.tool or 'Manual' }}</td>
                        <td>{{ task.findings_count }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </section>
        </div>

        <footer>
            <p>Generated by EHPA Task 1 - Backend Orchestration System</p>
            <p>Powered by Claude LLM and MCP Tool Framework</p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                This report is confidential and intended only for authorized recipients.
            </p>
        </footer>
    </div>
</body>
</html>
"""


async def generate_report(session: Session) -> Path:
    """
    Generate comprehensive penetration test report

    Args:
        session: Completed penetration test session

    Returns:
        Path to generated report file
    """
    logger.info(f"Generating report for session: {session.session_id}")

    # Prepare report directory
    reports_dir = Path(config.settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Get analysis from session metadata
    analysis = session.metadata.get('final_analysis', {})

    # Categorize vulnerabilities
    vulnerabilities_by_severity = {
        'critical': session.get_vulnerabilities_by_severity(SeverityLevel.CRITICAL),
        'high': session.get_vulnerabilities_by_severity(SeverityLevel.HIGH),
        'medium': session.get_vulnerabilities_by_severity(SeverityLevel.MEDIUM),
        'low': session.get_vulnerabilities_by_severity(SeverityLevel.LOW),
        'informational': session.get_vulnerabilities_by_severity(SeverityLevel.INFORMATIONAL)
    }

    # Prepare template data
    template_data = {
        'session': session,
        'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'duration': f"{session.get_duration_minutes() or 0:.1f} minutes",
        'scope': ', '.join(session.scope),
        'analysis': analysis,
        'vulnerabilities': [v.model_dump() for v in session.vulnerabilities],
        'critical_count': len(vulnerabilities_by_severity['critical']),
        'high_count': len(vulnerabilities_by_severity['high']),
        'medium_count': len(vulnerabilities_by_severity['medium']),
        'low_count': len(vulnerabilities_by_severity['low']),
    }

    # Generate HTML report
    template = Template(HTML_REPORT_TEMPLATE)
    html_content = template.render(**template_data)

    # Save HTML report
    report_filename = f"pentest_report_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    report_path = reports_dir / report_filename

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"HTML report generated: {report_path}")

    # Also generate JSON report for programmatic access
    json_filename = f"pentest_report_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_path = reports_dir / json_filename

    json_data = {
        'session_id': session.session_id,
        'target': session.target,
        'generated_at': datetime.utcnow().isoformat(),
        'statistics': session.get_statistics(),
        'vulnerabilities': template_data['vulnerabilities'],
        'analysis': analysis,
        'target_info': session.target_info.model_dump() if session.target_info else {}
    }

    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)

    logger.info(f"JSON report generated: {json_path}")

    return report_path
