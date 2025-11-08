"""
Reconnaissance Agent
Automates Phase 1: Information Gathering and Target Discovery

Tools: nmap, amass, subfinder, theharvester, shodan, whois
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReconAgent:
    """
    Reconnaissance Agent - Phase 1

    Responsibilities:
    - Discover hosts, subdomains, and network topology
    - Identify open ports and running services
    - Collect OSINT data about the target
    - Map the attack surface
    """

    def __init__(self, orchestrator):
        """
        Initialize Reconnaissance Agent

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
        Execute complete reconnaissance phase

        Args:
            session_id: Penetration test session ID

        Returns:
            Phase execution results with discovered assets
        """
        self.logger.info(f"🔍 Starting Reconnaissance Phase for session {session_id}")

        session = self.orchestrator.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        results = {
            'phase': 'reconnaissance',
            'session_id': session_id,
            'target': session.target,
            'started_at': datetime.utcnow().isoformat(),
            'tools_executed': [],
            'assets_discovered': {
                'hosts': [],
                'ports': [],
                'services': [],
                'subdomains': [],
                'emails': [],
                'technologies': []
            },
            'findings': []
        }

        try:
            # Step 1: Network Discovery with nmap
            nmap_results = await self._run_network_discovery(session)
            results['tools_executed'].append('nmap')
            if nmap_results:
                results['assets_discovered']['hosts'].extend(nmap_results.get('hosts', []))
                results['assets_discovered']['ports'].extend(nmap_results.get('ports', []))
                results['assets_discovered']['services'].extend(nmap_results.get('services', []))

            # Step 2: Subdomain Discovery
            subdomain_results = await self._run_subdomain_discovery(session)
            results['tools_executed'].extend(['amass', 'subfinder'])
            if subdomain_results:
                results['assets_discovered']['subdomains'].extend(subdomain_results.get('subdomains', []))

            # Step 3: OSINT Collection
            osint_results = await self._run_osint_collection(session)
            results['tools_executed'].append('theharvester')
            if osint_results:
                results['assets_discovered']['emails'].extend(osint_results.get('emails', []))
                results['assets_discovered']['hosts'].extend(osint_results.get('hosts', []))

            # Step 4: Technology Detection
            tech_results = await self._detect_technologies(session)
            if tech_results:
                results['assets_discovered']['technologies'].extend(tech_results.get('technologies', []))

            # Step 5: Analyze results using LLM
            analysis = await self._analyze_reconnaissance_results(session, results)
            results['analysis'] = analysis
            results['next_steps'] = analysis.get('recommendations', [])

            # Update session with discovered assets
            self._update_session_assets(session, results['assets_discovered'])

            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()

            self.logger.info(f"✅ Reconnaissance phase completed: "
                           f"{len(results['assets_discovered']['hosts'])} hosts, "
                           f"{len(results['assets_discovered']['subdomains'])} subdomains discovered")

        except Exception as e:
            self.logger.error(f"❌ Reconnaissance phase failed: {e}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['completed_at'] = datetime.utcnow().isoformat()

        return results

    async def _run_network_discovery(self, session) -> Dict[str, Any]:
        """
        Run network discovery using nmap

        Args:
            session: Session object

        Returns:
            Dictionary with discovered hosts, ports, and services
        """
        self.logger.info(f"Running network discovery on {session.target}")

        try:
            # Generate nmap command using LLM
            command_request = {
                'tool': 'nmap',
                'target': session.target,
                'objective': 'Discover live hosts, open ports, and running services',
                'scan_type': 'comprehensive'
            }

            command_spec = await self.generation.generate_command(command_request)

            # Execute nmap via tool registry or MCP
            tool = self.orchestrator.tools.get('nmap')
            if not tool:
                self.logger.warning("nmap tool not available, skipping network discovery")
                return {}

            # Execute tool
            raw_output = await tool.execute({
                'target': session.target,
                'ports': command_spec.get('ports', '1-1000'),
                'scan_type': command_spec.get('scan_type', 'syn'),
                'service_detection': True,
                'os_detection': True
            })

            # Parse results using LLM
            parsed_results = await self.parsing.parse_tool_output(
                tool_name='nmap',
                raw_output=raw_output.get('output', ''),
                objective='Extract hosts, ports, services, and OS information'
            )

            return parsed_results

        except Exception as e:
            self.logger.error(f"Network discovery failed: {e}")
            return {}

    async def _run_subdomain_discovery(self, session) -> Dict[str, Any]:
        """
        Discover subdomains using amass and subfinder

        Args:
            session: Session object

        Returns:
            Dictionary with discovered subdomains
        """
        self.logger.info(f"Running subdomain discovery on {session.target}")

        # Extract base domain
        target_domain = session.target.replace('http://', '').replace('https://', '').split('/')[0]

        subdomains = []

        try:
            # Try amass via Hexstrike if available
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                amass_result = await self.orchestrator.hexstrike_client.execute_tool(
                    'amass',
                    {'domain': target_domain, 'passive': True}
                )

                if amass_result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='amass',
                        raw_output=amass_result.get('output', ''),
                        objective='Extract discovered subdomains'
                    )
                    subdomains.extend(parsed.get('subdomains', []))

            # Try subfinder via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                subfinder_result = await self.orchestrator.hexstrike_client.execute_tool(
                    'subfinder',
                    {'domain': target_domain}
                )

                if subfinder_result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='subfinder',
                        raw_output=subfinder_result.get('output', ''),
                        objective='Extract discovered subdomains'
                    )
                    subdomains.extend(parsed.get('subdomains', []))

            # Deduplicate
            unique_subdomains = list(set(subdomains))

            return {'subdomains': unique_subdomains}

        except Exception as e:
            self.logger.error(f"Subdomain discovery failed: {e}")
            return {'subdomains': []}

    async def _run_osint_collection(self, session) -> Dict[str, Any]:
        """
        Collect OSINT data using theharvester

        Args:
            session: Session object

        Returns:
            Dictionary with emails, hosts, and other OSINT data
        """
        self.logger.info(f"Running OSINT collection on {session.target}")

        target_domain = session.target.replace('http://', '').replace('https://', '').split('/')[0]

        try:
            # Use theharvester via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                harvester_result = await self.orchestrator.hexstrike_client.execute_tool(
                    'theharvester',
                    {
                        'domain': target_domain,
                        'sources': ['google', 'bing', 'duckduckgo'],
                        'limit': 500
                    }
                )

                if harvester_result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='theharvester',
                        raw_output=harvester_result.get('output', ''),
                        objective='Extract emails, hosts, and IPs'
                    )
                    return parsed

            return {'emails': [], 'hosts': []}

        except Exception as e:
            self.logger.error(f"OSINT collection failed: {e}")
            return {'emails': [], 'hosts': []}

    async def _detect_technologies(self, session) -> Dict[str, Any]:
        """
        Detect web technologies in use

        Args:
            session: Session object

        Returns:
            Dictionary with detected technologies
        """
        self.logger.info(f"Detecting technologies on {session.target}")

        try:
            # Use whatweb via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                whatweb_result = await self.orchestrator.hexstrike_client.execute_tool(
                    'whatweb',
                    {'url': session.target, 'aggression': 1}
                )

                if whatweb_result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='whatweb',
                        raw_output=whatweb_result.get('output', ''),
                        objective='Extract web technologies and versions'
                    )
                    return parsed

            return {'technologies': []}

        except Exception as e:
            self.logger.error(f"Technology detection failed: {e}")
            return {'technologies': []}

    async def _analyze_reconnaissance_results(
        self,
        session,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze reconnaissance results using LLM reasoning module

        Args:
            session: Session object
            results: Reconnaissance results

        Returns:
            Analysis with insights and recommendations
        """
        self.logger.info("Analyzing reconnaissance results with LLM")

        try:
            analysis = await self.reasoning.analyze_phase_results(
                phase='reconnaissance',
                session_context={
                    'target': session.target,
                    'scope': session.scope
                },
                phase_results=results,
                objective='Analyze reconnaissance data and recommend next steps'
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'summary': 'Analysis unavailable',
                'recommendations': ['Proceed to enumeration phase']
            }

    def _update_session_assets(self, session, assets: Dict[str, List]) -> None:
        """
        Update session with discovered assets

        Args:
            session: Session object
            assets: Dictionary of discovered assets
        """
        # Store assets in session metadata
        if not hasattr(session, 'discovered_assets'):
            session.discovered_assets = {
                'hosts': [],
                'ports': [],
                'services': [],
                'subdomains': [],
                'emails': [],
                'technologies': []
            }

        # Merge new assets
        for key, values in assets.items():
            if key in session.discovered_assets:
                session.discovered_assets[key].extend(values)
                # Deduplicate
                session.discovered_assets[key] = list(set(session.discovered_assets[key]))

        # Save session
        session.save()

        self.logger.info(f"Updated session with {sum(len(v) for v in assets.values())} new assets")
