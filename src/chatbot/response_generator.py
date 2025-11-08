"""
Response Generator - Generate contextual responses for chatbot
Formats responses, suggestions, and UI-ready output
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger


class ResponseGenerator:
    """
    Generate formatted responses for different chatbot scenarios

    Responsibilities:
    - Format scan results for chat
    - Generate progress updates
    - Create vulnerability alerts
    - Provide suggestions based on context
    - Format errors and warnings
    """

    def __init__(self, prompts_path: str = "./configs/chatbot_prompts.yaml"):
        self.logger = get_logger(__name__)

        # Load response templates
        self.templates = self._load_templates(prompts_path)

        # Severity emojis
        self.severity_emojis = {
            'critical': '=4',
            'high': '=',
            'medium': '=',
            'low': '=5',
            'informational': '9'
        }

        self.logger.info("Response Generator initialized")

    def _load_templates(self, path: str) -> Dict[str, Any]:
        """Load response templates from YAML"""
        try:
            templates_path = Path(path)
            if templates_path.exists():
                with open(templates_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('response_templates', {})
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            return {}

    def format_scan_started(
        self,
        scan_type: str,
        target: str,
        tool: str,
        phase: str,
        estimated_duration: str = "5-10 minutes"
    ) -> Dict[str, Any]:
        """Format response for scan initiation"""
        template = self.templates.get('scan_started', '')

        description = self._get_scan_description(tool)

        message = template.format(
            scan_type=scan_type,
            target=target,
            phase=phase,
            tool=tool,
            duration=estimated_duration,
            description=description
        )

        return {
            'message': message,
            'type': 'scan_started',
            'data': {
                'target': target,
                'tool': tool,
                'phase': phase
            },
            'suggestions': [
                "Explain what this scan does",
                "Show me progress",
                "What are we looking for?"
            ]
        }

    def format_vulnerability_found(
        self,
        vulnerability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format response for vulnerability discovery"""
        template = self.templates.get('vulnerability_found', '')

        severity = vulnerability.get('severity', 'medium').lower()
        emoji = self.severity_emojis.get(severity, '')

        message = template.format(
            severity_emoji=emoji,
            severity=severity.upper(),
            title=vulnerability.get('title', 'Unknown Vulnerability'),
            location=vulnerability.get('location', 'N/A'),
            cvss_score=vulnerability.get('cvss_score', 'N/A'),
            description=vulnerability.get('description', 'No description available'),
            impact=vulnerability.get('impact', 'Impact assessment pending'),
            recommendation=vulnerability.get('recommendation', 'Review and remediate')
        )

        return {
            'message': message,
            'type': 'vulnerability_found',
            'data': vulnerability,
            'suggestions': [
                f"Explain {vulnerability.get('title', 'this vulnerability')}",
                "How critical is this?",
                "How do I fix it?",
                "Continue scanning"
            ]
        }

    def format_phase_complete(
        self,
        phase: str,
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format response for phase completion"""
        template = self.templates.get('phase_complete', '')

        key_findings = self._format_key_findings(
            summary.get('vulnerabilities', [])
        )

        next_steps = self._generate_next_steps(
            phase,
            summary.get('vulnerabilities_count', 0)
        )

        message = template.format(
            phase=phase.replace('_', ' ').title(),
            tasks_completed=summary.get('tasks_completed', 0),
            findings_count=summary.get('findings_count', 0),
            vulnerabilities_count=summary.get('vulnerabilities_count', 0),
            duration_minutes=summary.get('duration_minutes', 0),
            key_findings=key_findings,
            next_steps=next_steps,
            next_phase=self._get_next_phase(phase)
        )

        return {
            'message': message,
            'type': 'phase_complete',
            'data': summary,
            'suggestions': [
                "Show all findings",
                "What's next?",
                "Generate report"
            ]
        }

    def format_progress_update(
        self,
        progress: float,
        current_task: str,
        completed_count: int,
        total_count: int,
        latest_finding: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format progress update message"""
        template = self.templates.get('progress_update', '')

        latest_text = f"\n\n**Latest:** {latest_finding}" if latest_finding else ""

        message = template.format(
            progress=int(progress),
            current_task=current_task,
            completed_count=completed_count,
            total_count=total_count,
            latest_finding=latest_text
        )

        return {
            'message': message,
            'type': 'progress_update',
            'data': {
                'progress': progress,
                'current_task': current_task,
                'completed': completed_count,
                'total': total_count
            },
            'suggestions': [
                "Show current findings",
                "Pause scan",
                "What have we found?"
            ]
        }

    def format_results_summary(
        self,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format comprehensive results summary"""
        template = self.templates.get('results_summary', '')

        # Format top vulnerabilities
        top_vulns = self._format_top_vulnerabilities(
            session_data.get('vulnerabilities', [])
        )

        message = template.format(
            target=session_data.get('target', 'N/A'),
            phase=session_data.get('phase', 'N/A'),
            progress=session_data.get('progress', 0),
            critical_count=session_data.get('critical_count', 0),
            high_count=session_data.get('high_count', 0),
            medium_count=session_data.get('medium_count', 0),
            low_count=session_data.get('low_count', 0),
            info_count=session_data.get('info_count', 0),
            top_vulnerabilities=top_vulns
        )

        return {
            'message': message,
            'type': 'results_summary',
            'data': session_data,
            'suggestions': [
                "Explain most critical issue",
                "Generate full report",
                "What should I fix first?"
            ]
        }

    def format_error(
        self,
        error_message: str,
        explanation: str = "",
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Format error message"""
        template = self.templates.get('error_occurred', '')

        if not suggestions:
            suggestions = [
                "Try again",
                "Check configuration",
                "View documentation"
            ]

        suggestion_text = "\n".join(f"- {s}" for s in suggestions)

        message = template.format(
            error_message=error_message,
            explanation=explanation or "An unexpected error occurred.",
            suggestions=suggestion_text
        )

        return {
            'message': message,
            'type': 'error',
            'data': {'error': error_message},
            'suggestions': suggestions
        }

    def format_confirmation_required(
        self,
        action: str,
        risk_level: str,
        warning: str
    ) -> Dict[str, Any]:
        """Format confirmation request"""
        template = self.templates.get('confirmation_required', '')

        message = template.format(
            action=action,
            risk_level=risk_level,
            warning=warning
        )

        return {
            'message': message,
            'type': 'confirmation_required',
            'data': {
                'action': action,
                'risk_level': risk_level
            },
            'suggestions': [
                "Confirm",
                "Cancel",
                "Tell me more about this action"
            ]
        }

    def format_greeting(self) -> Dict[str, Any]:
        """Format greeting message"""
        message = """Hello! I'm EHPA, your Ethical Hacking Personal Assistant.

I can help you with:
" Running security scans and tests
" Explaining security concepts
" Interpreting vulnerability findings
" Recommending next steps

Try asking me to "scan a target" or "explain SQL injection"!"""

        return {
            'message': message,
            'type': 'greeting',
            'data': {},
            'suggestions': [
                "Start a scan",
                "What can you do?",
                "Explain reconnaissance"
            ]
        }

    def format_help(self) -> Dict[str, Any]:
        """Format help message"""
        message = """**EHPA Capabilities:**

**=
 Security Testing:**
- "Scan target.com"
- "Run nmap on 192.168.1.1"
- "Test for SQL injection"
- "Enumerate directories"

**= Education:**
- "What is XSS?"
- "Explain nmap"
- "How does SQL injection work?"

**= Results:**
- "Show findings"
- "What did we discover?"
- "What's the most critical issue?"

**< Guidance:**
- "What should I do next?"
- "Prioritize vulnerabilities"
- "Generate report"

What would you like to do?"""

        return {
            'message': message,
            'type': 'help',
            'data': {},
            'suggestions': [
                "Start a scan",
                "Explain a concept",
                "Show example commands"
            ]
        }

    def _get_scan_description(self, tool: str) -> str:
        """Get description for scan tool"""
        descriptions = {
            'nmap': 'Network reconnaissance to discover open ports and services',
            'nikto': 'Web vulnerability scanning for common security issues',
            'sqlmap': 'SQL injection detection and exploitation',
            'gobuster': 'Directory and file enumeration to find hidden resources',
            'nuclei': 'Template-based vulnerability scanning',
            'metasploit': 'Exploitation framework for validating vulnerabilities'
        }
        return descriptions.get(tool.lower(), 'Security testing')

    def _format_key_findings(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Format key findings list"""
        if not vulnerabilities:
            return "No vulnerabilities discovered."

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'informational': 4}
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: severity_order.get(v.get('severity', 'low').lower(), 5)
        )

        findings = []
        for vuln in sorted_vulns[:3]:  # Top 3
            severity = vuln.get('severity', 'medium').lower()
            emoji = self.severity_emojis.get(severity, '')
            findings.append(f"{emoji} {vuln.get('title', 'Unknown issue')}")

        return "\n".join(findings)

    def _format_top_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Format top vulnerabilities for display"""
        if not vulnerabilities:
            return "No vulnerabilities found."

        # Get critical and high only
        critical_high = [
            v for v in vulnerabilities
            if v.get('severity', '').lower() in ['critical', 'high']
        ]

        if not critical_high:
            return "No critical or high severity vulnerabilities found."

        result = []
        for vuln in critical_high[:5]:  # Top 5
            severity = vuln.get('severity', 'medium').lower()
            emoji = self.severity_emojis.get(severity, '')
            title = vuln.get('title', 'Unknown')
            location = vuln.get('location', 'N/A')
            result.append(f"{emoji} **{title}** - {location}")

        return "\n".join(result)

    def _generate_next_steps(self, current_phase: str, vuln_count: int) -> str:
        """Generate next steps recommendations"""
        steps = []

        if current_phase == 'reconnaissance':
            steps.append("1. Review discovered services and ports")
            steps.append("2. Proceed to Enumeration phase for detailed analysis")
            steps.append("3. Identify potential attack vectors")

        elif current_phase == 'enumeration':
            steps.append("1. Analyze enumerated users and directories")
            steps.append("2. Move to Vulnerability Scanning phase")
            steps.append("3. Focus on services with known weaknesses")

        elif current_phase == 'vulnerability_scanning':
            if vuln_count > 0:
                steps.append("1. Review and prioritize discovered vulnerabilities")
                steps.append("2. Proceed to Exploitation phase (with approval)")
                steps.append("3. Prepare proof-of-concept for critical issues")
            else:
                steps.append("1. Verify scan coverage is complete")
                steps.append("2. Consider manual testing techniques")
                steps.append("3. Proceed to reporting if satisfied")

        elif current_phase == 'exploitation':
            steps.append("1. Document all successful exploits")
            steps.append("2. Move to Post-Exploitation phase (with approval)")
            steps.append("3. Assess full impact of vulnerabilities")

        elif current_phase == 'post_exploitation':
            steps.append("1. Complete evidence collection")
            steps.append("2. Remove all persistence mechanisms")
            steps.append("3. Generate comprehensive report")

        else:
            steps.append("1. Review all findings")
            steps.append("2. Continue current phase activities")
            steps.append("3. Request guidance if unsure")

        return "\n".join(steps)

    def _get_next_phase(self, current_phase: str) -> str:
        """Get next phase name"""
        phase_order = [
            'reconnaissance',
            'enumeration',
            'vulnerability_scanning',
            'exploitation',
            'post_exploitation',
            'reporting'
        ]

        try:
            current_idx = phase_order.index(current_phase.lower())
            if current_idx < len(phase_order) - 1:
                return phase_order[current_idx + 1].replace('_', ' ').title()
        except ValueError:
            pass

        return "Next Phase"

    def generate_suggestions(
        self,
        context: str,
        session_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate contextual suggestions based on current state"""
        suggestions = []

        if context == 'after_scan_start':
            suggestions = [
                "Explain what this scan does",
                "Show me results so far",
                "What are we looking for?"
            ]

        elif context == 'after_vulnerability_found':
            suggestions = [
                "Explain this vulnerability",
                "How critical is this?",
                "How do I fix it?",
                "Test this vulnerability"
            ]

        elif context == 'after_phase_complete':
            suggestions = [
                "Show all findings",
                "What's next?",
                "Generate report"
            ]

        elif context == 'general':
            suggestions = [
                "What should I do next?",
                "Explain a concept",
                "Show findings",
                "Help"
            ]

        # Add context-specific suggestions
        if session_data:
            phase = session_data.get('phase', '')
            if phase == 'reconnaissance':
                suggestions.append("Move to enumeration phase")
            elif phase == 'vulnerability_scanning':
                if session_data.get('vulnerabilities_count', 0) > 0:
                    suggestions.append("Exploit vulnerabilities")

        return suggestions[:4]  # Limit to 4 suggestions
