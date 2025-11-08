"""
Enumeration Agent
Automates Phase 2: Service Enumeration and Detailed Information Extraction

Tools: enum4linux, dnsenum, gobuster, dirb, ffuf
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnumAgent:
    """
    Enumeration Agent - Phase 2

    Responsibilities:
    - Enumerate services in detail (SMB, DNS, HTTP, etc.)
    - Directory and file discovery on web servers
    - Extract detailed service configurations
    - Identify potential entry points
    """

    def __init__(self, orchestrator):
        """
        Initialize Enumeration Agent

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
        Execute complete enumeration phase

        Args:
            session_id: Penetration test session ID

        Returns:
            Phase execution results with enumerated services
        """
        self.logger.info(f"🔎 Starting Enumeration Phase for session {session_id}")

        session = self.orchestrator.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        results = {
            'phase': 'enumeration',
            'session_id': session_id,
            'target': session.target,
            'started_at': datetime.utcnow().isoformat(),
            'tools_executed': [],
            'enumeration_data': {
                'smb_shares': [],
                'dns_records': [],
                'directories': [],
                'files': [],
                'api_endpoints': [],
                'users': [],
                'groups': []
            },
            'findings': []
        }

        try:
            # Get discovered assets from reconnaissance
            assets = getattr(session, 'discovered_assets', {})
            services = assets.get('services', [])

            # Step 1: SMB Enumeration (if SMB service found)
            if self._has_service(services, ['smb', '445', '139']):
                smb_results = await self._enumerate_smb(session)
                results['tools_executed'].append('enum4linux')
                if smb_results:
                    results['enumeration_data']['smb_shares'].extend(smb_results.get('shares', []))
                    results['enumeration_data']['users'].extend(smb_results.get('users', []))

            # Step 2: DNS Enumeration
            dns_results = await self._enumerate_dns(session)
            results['tools_executed'].append('dnsenum')
            if dns_results:
                results['enumeration_data']['dns_records'].extend(dns_results.get('records', []))

            # Step 3: Web Directory Enumeration (if HTTP/HTTPS service found)
            if self._has_service(services, ['http', 'https', '80', '443', '8080', '8443']):
                dir_results = await self._enumerate_directories(session)
                results['tools_executed'].extend(['gobuster', 'ffuf'])
                if dir_results:
                    results['enumeration_data']['directories'].extend(dir_results.get('directories', []))
                    results['enumeration_data']['files'].extend(dir_results.get('files', []))

            # Step 4: API Endpoint Discovery
            if self._is_web_target(session.target):
                api_results = await self._discover_api_endpoints(session)
                if api_results:
                    results['enumeration_data']['api_endpoints'].extend(api_results.get('endpoints', []))

            # Step 5: Analyze enumeration results using LLM
            analysis = await self._analyze_enumeration_results(session, results)
            results['analysis'] = analysis
            results['next_steps'] = analysis.get('recommendations', [])

            # Update session with enumeration data
            self._update_session_enumeration(session, results['enumeration_data'])

            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()

            self.logger.info(f"✅ Enumeration phase completed: "
                           f"{len(results['enumeration_data']['directories'])} directories, "
                           f"{len(results['enumeration_data']['files'])} files discovered")

        except Exception as e:
            self.logger.error(f"❌ Enumeration phase failed: {e}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['completed_at'] = datetime.utcnow().isoformat()

        return results

    async def _enumerate_smb(self, session) -> Dict[str, Any]:
        """
        Enumerate SMB shares and users using enum4linux

        Args:
            session: Session object

        Returns:
            Dictionary with SMB enumeration results
        """
        self.logger.info(f"Enumerating SMB on {session.target}")

        try:
            # Execute enum4linux
            tool = self.orchestrator.tools.get('enum4linux')
            if tool:
                raw_output = await tool.execute({
                    'target': session.target,
                    'enum_all': True
                })

                # Parse results
                parsed = await self.parsing.parse_tool_output(
                    tool_name='enum4linux',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract SMB shares, users, groups, and configurations'
                )

                return parsed

            # Try via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                result = await self.orchestrator.hexstrike_client.execute_tool(
                    'enum4linux',
                    {'target': session.target, 'all': True}
                )

                if result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='enum4linux',
                        raw_output=result.get('output', ''),
                        objective='Extract SMB shares, users, groups'
                    )
                    return parsed

            return {}

        except Exception as e:
            self.logger.error(f"SMB enumeration failed: {e}")
            return {}

    async def _enumerate_dns(self, session) -> Dict[str, Any]:
        """
        Enumerate DNS records using dnsenum

        Args:
            session: Session object

        Returns:
            Dictionary with DNS records
        """
        self.logger.info(f"Enumerating DNS for {session.target}")

        target_domain = session.target.replace('http://', '').replace('https://', '').split('/')[0]

        try:
            # Try via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                result = await self.orchestrator.hexstrike_client.execute_tool(
                    'dnsenum',
                    {'domain': target_domain}
                )

                if result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='dnsenum',
                        raw_output=result.get('output', ''),
                        objective='Extract DNS records (A, MX, NS, TXT, etc.)'
                    )
                    return parsed

            return {}

        except Exception as e:
            self.logger.error(f"DNS enumeration failed: {e}")
            return {}

    async def _enumerate_directories(self, session) -> Dict[str, Any]:
        """
        Enumerate web directories and files using gobuster and ffuf

        Args:
            session: Session object

        Returns:
            Dictionary with discovered directories and files
        """
        self.logger.info(f"Enumerating directories on {session.target}")

        directories = []
        files = []

        try:
            # Try gobuster first
            tool = self.orchestrator.tools.get('gobuster')
            if tool:
                raw_output = await tool.execute({
                    'url': session.target,
                    'wordlist': '/usr/share/wordlists/dirb/common.txt',
                    'mode': 'dir',
                    'extensions': 'php,html,txt,js,json,xml'
                })

                parsed = await self.parsing.parse_tool_output(
                    tool_name='gobuster',
                    raw_output=raw_output.get('output', ''),
                    objective='Extract discovered directories and files with status codes'
                )

                directories.extend(parsed.get('directories', []))
                files.extend(parsed.get('files', []))

            # Try ffuf via Hexstrike for additional coverage
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                result = await self.orchestrator.hexstrike_client.execute_tool(
                    'ffuf',
                    {
                        'url': f"{session.target}/FUZZ",
                        'wordlist': '/usr/share/wordlists/dirb/common.txt',
                        'extensions': 'php,html,txt,js'
                    }
                )

                if result.get('status') == 'success':
                    parsed = await self.parsing.parse_tool_output(
                        tool_name='ffuf',
                        raw_output=result.get('output', ''),
                        objective='Extract discovered URLs and response sizes'
                    )
                    directories.extend(parsed.get('directories', []))
                    files.extend(parsed.get('files', []))

            return {
                'directories': list(set(directories)),
                'files': list(set(files))
            }

        except Exception as e:
            self.logger.error(f"Directory enumeration failed: {e}")
            return {'directories': [], 'files': []}

    async def _discover_api_endpoints(self, session) -> Dict[str, Any]:
        """
        Discover API endpoints

        Args:
            session: Session object

        Returns:
            Dictionary with discovered API endpoints
        """
        self.logger.info(f"Discovering API endpoints on {session.target}")

        try:
            # Common API paths to check
            api_paths = [
                '/api', '/api/v1', '/api/v2',
                '/rest', '/graphql',
                '/swagger', '/swagger.json', '/swagger/v1/swagger.json',
                '/api-docs', '/api/docs',
                '/openapi.json'
            ]

            endpoints = []

            # Use ffuf or custom checks via Hexstrike
            if hasattr(self.orchestrator, 'hexstrike_client') and self.orchestrator.hexstrike_client:
                for path in api_paths:
                    result = await self.orchestrator.hexstrike_client.execute_tool(
                        'curl',
                        {'url': f"{session.target}{path}", 'method': 'GET'}
                    )

                    if result.get('status') == 'success':
                        # Check if endpoint exists (200, 301, 302, etc.)
                        endpoints.append({'path': path, 'found': True})

            return {'endpoints': endpoints}

        except Exception as e:
            self.logger.error(f"API endpoint discovery failed: {e}")
            return {'endpoints': []}

    async def _analyze_enumeration_results(
        self,
        session,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze enumeration results using LLM reasoning module

        Args:
            session: Session object
            results: Enumeration results

        Returns:
            Analysis with insights and recommendations
        """
        self.logger.info("Analyzing enumeration results with LLM")

        try:
            analysis = await self.reasoning.analyze_phase_results(
                phase='enumeration',
                session_context={
                    'target': session.target,
                    'scope': session.scope
                },
                phase_results=results,
                objective='Identify high-value targets and potential vulnerabilities'
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'summary': 'Analysis unavailable',
                'recommendations': ['Proceed to vulnerability scanning phase']
            }

    def _has_service(self, services: List, keywords: List[str]) -> bool:
        """Check if any service matches the keywords"""
        if not services:
            return False

        for service in services:
            service_str = str(service).lower()
            if any(keyword.lower() in service_str for keyword in keywords):
                return True

        return False

    def _is_web_target(self, target: str) -> bool:
        """Check if target is a web application"""
        return target.startswith('http://') or target.startswith('https://')

    def _update_session_enumeration(self, session, enum_data: Dict[str, List]) -> None:
        """
        Update session with enumeration data

        Args:
            session: Session object
            enum_data: Dictionary of enumeration data
        """
        # Store enumeration data in session metadata
        if not hasattr(session, 'enumeration_data'):
            session.enumeration_data = {
                'smb_shares': [],
                'dns_records': [],
                'directories': [],
                'files': [],
                'api_endpoints': [],
                'users': [],
                'groups': []
            }

        # Merge new data
        for key, values in enum_data.items():
            if key in session.enumeration_data:
                session.enumeration_data[key].extend(values)

        # Save session
        session.save()

        self.logger.info(f"Updated session with enumeration data")
