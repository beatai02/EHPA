"""
Vulnerability Scanning Agent
Automates Phase 3: Vulnerability Scanning and Weakness Identification

Tools: nikto, nuclei, wpscan, nmap (vuln scripts)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VulnAgent:
    """
    Vulnerability Scanning Agent - Phase 3

    Responsibilities:
    - Scan for known vulnerabilities
    - Identify security weaknesses
    - Classify vulnerabilities by severity
    - Provide remediation recommendations
    """

    def __init__(self, orchestrator):
        """
        Initialize Vulnerability Scanning Agent

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
        Execute complete vulnerability scanning phase

        Args:
            session_id: Penetration test session ID

        Returns:
            Phase execution results with discovered vulnerabilities
        """
        self.logger.info(f"🔬 Starting Vulnerability Scanning Phase for session {session_id}")

        session = self.orchestrator.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        results = {
            'phase': 'vulnerability_scanning',
            'session_id': session_id,
            'target': session.target,
            'started_at': datetime.utcnow().isoformat(),
            'tools_executed': [],
            'vulnerabilities': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'informational': []
            },
            'findings': []
        }

        try:
            # Step 1: Web Vulnerability Scanning with Nikto
            if self._is_web_target(session.target):
                nikto_results = await self._scan_with_nikto(session)
                results['tools_executed'].append('nikto')
                if nikto_results:
                    self._categorize_vulnerabilities(
                        results['vulnerabilities'],
                        nikto_results.get('vulnerabilities', [])
                    )

            # Step 2: Template-based scanning with Nuclei
            if self._is_web_target(session.target):
                nuclei_results = await self._scan_with_nuclei(session)
                results['tools_executed'].append('nuclei')
                if nuclei_results:
                    self._categorize_vulnerabilities(
                        results['vulnerabilities'],
                        nuclei_results.get('vulnerabilities', [])
                    )

            # Step 3: WordPress scanning (if WordPress detected)
            if self._is_wordpress_site(session):
                wpscan_results = await self._scan_wordpress(session)
                results['tools_executed'].append('wpscan')
                if wpscan_results:
                    self._categorize_vulnerabilities(
                        results['vulnerabilities'],
                        wpscan_results.get('vulnerabilities', [])
                    )

            # Step 4: NSE vulnerability scripts with nmap
            nmap_vuln_results = await self._scan_with_nmap_vuln(session)
            results['tools_executed'].append('nmap')
            if nmap_vuln_results:
                self._categorize_vulnerabilities(
                    results['vulnerabilities'],
                    nmap_vuln_results.get('vulnerabilities', [])
                )

            # Step 5: Analyze vulnerabilities using LLM
            analysis = await self._analyze_vulnerabilities(session, results)
            results['analysis'] = analysis
            results['next_steps'] = analysis.get('recommendations', [])
            results['risk_score'] = analysis.get('risk_score', 0)

            # Update session with vulnerabilities
            self._update_session_vulnerabilities(session, results['vulnerabilities'])

            # Calculate statistics
            total_vulns = sum(len(v) for v in results['vulnerabilities'].values())
            results['statistics'] = {
                'total_vulnerabilities': total_vulns,
                'critical_count': len(results['vulnerabilities']['critical']),
                'high_count': len(results['vulnerabilities']['high']),
                'medium_count': len(results['vulnerabilities']['medium']),
                'low_count': len(results['vulnerabilities']['low']),
                'info_count': len(results['vulnerabilities']['informational'])
            }

            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()

            self.logger.info(f"✅ Vulnerability scanning completed: {total_vulns} vulnerabilities found")

        except Exception as e:
            self.logger.error(f"❌ Vulnerability scanning phase failed: {e}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['completed_at'] = datetime.utcnow().isoformat()

        return results

    async def _scan_with_nikto(self, session) -> Dict[str, Any]:
        """
        Scan web application with Nikto

        Args:
            session: Session object

        Returns:
            Dictionary with discovered vulnerabilities
        """
        self.logger.info(f"Running Nikto scan on {session.target}")

        try:
            # Execute nikto
            tool = self.orchestrator.tools.get('nikto')
            if tool:
                raw_output = await tool.execute({
                    'target': session.target,
                    'port': 443 if session.target.startswith('https') else 80,
                    'ssl': session.target.startswith('https')
                })

                # Parse results
                parsed = await self.parsing.parse_tool_output(
                    tool_name='nikto',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract vulnerabilities with severity levels'
                )

                return parsed

            return {}

        except Exception as e:
            self.logger.error(f"Nikto scan failed: {e}")
            return {}

    async def _scan_with_nuclei(self, session) -> Dict[str, Any]:
        """
        Scan with Nuclei templates

        Args:
            session: Session object

        Returns:
            Dictionary with discovered vulnerabilities
        """
        self.logger.info(f"Running Nuclei scan on {session.target}")

        try:
            # Execute nuclei
            tool = self.orchestrator.tools.get('nuclei')
            if tool:
                raw_output = await tool.execute({
                    'target': session.target,
                    'templates': 'all',
                    'severity': ['critical', 'high', 'medium']
                })

                # Parse results
                parsed = await self.parsing.parse_tool_output(
                    tool_name='nuclei',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract vulnerabilities with template info and severity'
                )

                return parsed

            # Try via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                result = await self.orchestrator.hexstrike_client.execute_tool(
                    'nuclei',
                    {'url': session.target, 'templates': 'cves,vulnerabilities'}
                )

                if result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='nuclei',
                        raw_output=result.get('output', ''),
                        objective='Extract CVEs and vulnerabilities'
                    )
                    return parsed

            return {}

        except Exception as e:
            self.logger.error(f"Nuclei scan failed: {e}")
            return {}

    async def _scan_wordpress(self, session) -> Dict[str, Any]:
        """
        Scan WordPress site with WPScan

        Args:
            session: Session object

        Returns:
            Dictionary with WordPress vulnerabilities
        """
        self.logger.info(f"Running WPScan on {session.target}")

        try:
            # Execute wpscan
            tool = self.orchestrator.tools.get('wpscan')
            if tool:
                raw_output = await tool.execute({
                    'url': session.target,
                    'enumerate': 'vp,vt,u',  # Vulnerable plugins, themes, users
                    'api_token': None  # Uses free API
                })

                # Parse results
                parsed = await self.parsing.parse_tool_output(
                    tool_name='wpscan',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract WordPress vulnerabilities in core, plugins, and themes'
                )

                return parsed

            # Try via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                result = await self.orchestrator.hexstrike_client.execute_tool(
                    'wpscan',
                    {'url': session.target, 'enumerate': 'vp,vt'}
                )

                if result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='wpscan',
                        raw_output=result.get('output', ''),
                        objective='Extract WordPress vulnerabilities'
                    )
                    return parsed

            return {}

        except Exception as e:
            self.logger.error(f"WPScan failed: {e}")
            return {}

    async def _scan_with_nmap_vuln(self, session) -> Dict[str, Any]:
        """
        Run nmap vulnerability scripts

        Args:
            session: Session object

        Returns:
            Dictionary with discovered vulnerabilities
        """
        self.logger.info(f"Running nmap vulnerability scripts on {session.target}")

        try:
            # Execute nmap with vuln scripts
            tool = self.orchestrator.tools.get('nmap')
            if tool:
                raw_output = await tool.execute({
                    'target': session.target,
                    'scripts': 'vuln',
                    'service_detection': True
                })

                # Parse results
                parsed = await self.parsing.parse_tool_output(
                    tool_name='nmap',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract vulnerabilities from NSE scripts'
                )

                return parsed

            return {}

        except Exception as e:
            self.logger.error(f"Nmap vulnerability scan failed: {e}")
            return {}

    async def _analyze_vulnerabilities(
        self,
        session,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze vulnerabilities using LLM reasoning module

        Args:
            session: Session object
            results: Vulnerability scan results

        Returns:
            Analysis with risk assessment and prioritization
        """
        self.logger.info("Analyzing vulnerabilities with LLM")

        try:
            analysis = await self.reasoning.analyze_phase_results(
                phase='vulnerability_scanning',
                session_context={
                    'target': session.target,
                    'scope': session.scope
                },
                phase_results=results,
                objective='Assess risk, prioritize vulnerabilities, and recommend exploitation targets'
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'summary': 'Analysis unavailable',
                'recommendations': ['Review critical and high severity vulnerabilities'],
                'risk_score': 5
            }

    def _categorize_vulnerabilities(
        self,
        categories: Dict[str, List],
        vulnerabilities: List[Dict]
    ) -> None:
        """
        Categorize vulnerabilities by severity

        Args:
            categories: Dictionary to store categorized vulnerabilities
            vulnerabilities: List of vulnerabilities to categorize
        """
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'informational').lower()

            if severity in categories:
                categories[severity].append(vuln)
            else:
                # Default to informational
                categories['informational'].append(vuln)

    def _is_web_target(self, target: str) -> bool:
        """Check if target is a web application"""
        return target.startswith('http://') or target.startswith('https://')

    def _is_wordpress_site(self, session) -> bool:
        """Check if target is a WordPress site"""
        # Check if WordPress was detected in enumeration or reconnaissance
        technologies = getattr(session, 'discovered_assets', {}).get('technologies', [])

        for tech in technologies:
            if 'wordpress' in str(tech).lower() or 'wp-' in str(tech).lower():
                return True

        return False

    def _update_session_vulnerabilities(
        self,
        session,
        vulnerabilities: Dict[str, List]
    ) -> None:
        """
        Update session with discovered vulnerabilities

        Args:
            session: Session object
            vulnerabilities: Dictionary of categorized vulnerabilities
        """
        # Convert to session Vulnerability objects
        from ..core.session import Vulnerability, VulnerabilitySeverity

        for severity, vulns in vulnerabilities.items():
            for vuln_data in vulns:
                vuln = Vulnerability(
                    title=vuln_data.get('title', 'Unknown Vulnerability'),
                    description=vuln_data.get('description', ''),
                    severity=VulnerabilitySeverity(severity),
                    cvss_score=vuln_data.get('cvss_score', 0.0),
                    cve_id=vuln_data.get('cve_id'),
                    affected_component=vuln_data.get('component', session.target),
                    evidence=vuln_data.get('evidence', ''),
                    remediation=vuln_data.get('remediation', 'No remediation available')
                )

                session.add_vulnerability(vuln)

        # Save session
        session.save()

        total = sum(len(v) for v in vulnerabilities.values())
        self.logger.info(f"Updated session with {total} vulnerabilities")
