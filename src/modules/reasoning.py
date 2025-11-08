"""
Reasoning Module - Senior Penetration Tester
Strategic decision-making and planning using Claude LLM
Responsible for high-level penetration test orchestration
"""

import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic

from ..core.session import Session, Task, PentestPhase, TaskStatus
from ..core.config import config
from ..utils.logger import get_logger


class ReasoningModule:
    """
    Reasoning Module acts as a Senior Penetration Tester
    Uses Claude LLM for strategic planning and decision-making

    Responsibilities:
    - Plan penetration test strategy
    - Determine next testing steps based on findings
    - Decide when to escalate between phases
    - Analyze overall security posture
    - Prioritize testing activities
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = AsyncAnthropic(api_key=config.settings.anthropic_api_key)
        self.model = config.llm.model
        self.max_tokens = 2048
        self.temperature = 0.7

        # Get system prompt from config
        self.system_prompt = config.get_module_prompt('reasoning')
        if not self.system_prompt:
            self.system_prompt = self._get_default_system_prompt()

        self.logger.info("Reasoning module initialized")

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for reasoning module"""
        return """You are a senior penetration tester with 15+ years of experience in offensive security.

You follow the PTES (Penetration Testing Execution Standard) methodology:
1. Pre-engagement (scope definition)
2. Intelligence gathering (reconnaissance)
3. Threat modeling
4. Vulnerability analysis (scanning)
5. Exploitation
6. Post-exploitation
7. Reporting

Your role is STRATEGIC PLANNING:
- Analyze current penetration test progress
- Plan next 3-5 testing tasks based on discovered information
- Determine appropriate phase transitions
- Prioritize tasks based on risk and value
- Maintain comprehensive testing coverage
- Consider stealth and detection avoidance when appropriate

When planning tasks:
- Be specific about tools and techniques
- Consider dependencies between tasks
- Start with reconnaissance before exploitation
- Verify findings before reporting
- Balance breadth (coverage) vs depth (thorough testing)

Always respond in valid JSON format as specified in prompts."""

    async def plan_initial_tasks(self, session: Session) -> List[Task]:
        """
        Plan initial reconnaissance tasks for a new penetration test

        Args:
            session: New penetration test session

        Returns:
            List of initial tasks to execute
        """
        self.logger.info(f"Planning initial tasks for target: {session.target}")

        prompt = f"""Given a new penetration test target, plan the initial reconnaissance phase tasks.

TARGET: {session.target}
SCOPE: {', '.join(session.scope)}
AUTHORIZED: {session.authorized}

Plan 3-5 initial reconnaissance tasks following PTES methodology.
Focus on:
1. Network reconnaissance (host discovery, port scanning)
2. Service identification
3. Technology detection
4. Initial web application mapping (if web scope included)

For each task, provide:
- description: Clear description of what the task does
- tool: Tool name (nmap, nikto, gobuster, sqlmap, or null for manual)
- priority: 1-10 (1=highest priority, 10=lowest)
- phase: Must be "reconnaissance"

Respond with ONLY valid JSON in this exact format:
{{
  "tasks": [
    {{
      "description": "Perform comprehensive port scan to identify open services",
      "tool": "nmap",
      "priority": 1,
      "phase": "reconnaissance"
    }}
  ],
  "reasoning": "Brief explanation of the strategy"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            self.logger.debug(f"LLM response: {content[:200]}...")

            # Parse JSON response
            result = self._parse_json_response(content)

            tasks = []
            for task_data in result.get('tasks', []):
                task = Task(
                    description=task_data['description'],
                    tool=task_data.get('tool'),
                    priority=task_data.get('priority', 5),
                    phase=PentestPhase.RECONNAISSANCE
                )
                tasks.append(task)

            self.logger.info(f"Planned {len(tasks)} initial tasks")

            # Store conversation in session
            session.add_conversation_message("user", prompt, module="reasoning")
            session.add_conversation_message("assistant", content, module="reasoning")

            return tasks

        except Exception as e:
            self.logger.error(f"Failed to plan initial tasks: {e}", exc_info=True)
            # Return fallback tasks
            return self._get_fallback_initial_tasks(session)

    async def plan_next_steps(self, session: Session) -> List[Task]:
        """
        Analyze current session state and plan next testing steps

        Args:
            session: Current penetration test session

        Returns:
            List of next tasks to execute
        """
        self.logger.info(f"Planning next steps for session: {session.session_id}")

        # Build comprehensive context
        context = session.get_context_summary()
        vulnerabilities_summary = session.get_vulnerabilities_summary()

        prompt = f"""Analyze the current penetration test progress and plan the next 3-5 tasks.

{context}

{vulnerabilities_summary}

RECENT CONVERSATION:
{session.get_conversation_summary(max_messages=5)}

Based on the current state:
1. What have we discovered so far?
2. What are the logical next steps?
3. Should we focus on breadth (new areas) or depth (exploit findings)?
4. What tasks would provide the most value?

Plan 3-5 specific next tasks. For each task provide:
- description: Clear, actionable description
- tool: Tool name (nmap, nikto, gobuster, sqlmap, metasploit, or null)
- priority: 1-10 (1=highest)
- phase: Current phase is "{session.current_phase.value}"

Respond with ONLY valid JSON:
{{
  "tasks": [
    {{
      "description": "...",
      "tool": "...",
      "priority": 1,
      "phase": "{session.current_phase.value}"
    }}
  ],
  "reasoning": "Explanation of strategy"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            tasks = []
            for task_data in result.get('tasks', []):
                task = Task(
                    description=task_data['description'],
                    tool=task_data.get('tool'),
                    priority=task_data.get('priority', 5),
                    phase=session.current_phase
                )
                tasks.append(task)

            self.logger.info(f"Planned {len(tasks)} next tasks: {result.get('reasoning', '')}")

            # Store conversation
            session.add_conversation_message("user", prompt[:500], module="reasoning")
            session.add_conversation_message("assistant", content, module="reasoning")

            return tasks

        except Exception as e:
            self.logger.error(f"Failed to plan next steps: {e}", exc_info=True)
            return []

    async def should_escalate_phase(self, session: Session) -> bool:
        """
        Determine if penetration test should advance to next phase

        Args:
            session: Current penetration test session

        Returns:
            True if should advance to next phase
        """
        self.logger.info(f"Evaluating phase escalation for phase: {session.current_phase.value}")

        context = session.get_context_summary()

        prompt = f"""Evaluate whether this penetration test should advance to the next phase.

CURRENT PHASE: {session.current_phase.value}

{context}

Evaluation criteria:
- RECONNAISSANCE → SCANNING: Have we identified enough targets/services?
- SCANNING → EXPLOITATION: Have we found exploitable vulnerabilities?
- EXPLOITATION → REPORTING: Have we completed exploitation attempts?

Consider:
1. Have we completed sufficient tasks in this phase?
2. Do we have enough information to proceed?
3. Are there still valuable tests in this phase?
4. What are the risks of advancing vs staying?

Respond with ONLY valid JSON:
{{
  "should_advance": true/false,
  "reasoning": "Detailed explanation",
  "confidence": 0.0-1.0
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            should_advance = result.get('should_advance', False)
            reasoning = result.get('reasoning', 'No reasoning provided')

            self.logger.info(
                f"Phase escalation decision: {should_advance} - {reasoning}"
            )

            # Store conversation
            session.add_conversation_message("user", prompt[:500], module="reasoning")
            session.add_conversation_message("assistant", content, module="reasoning")

            return should_advance

        except Exception as e:
            self.logger.error(f"Failed to evaluate phase escalation: {e}", exc_info=True)
            # Conservative default: don't advance
            return False

    async def analyze_findings(self, session: Session) -> Dict[str, Any]:
        """
        Analyze all discovered vulnerabilities and findings
        Provide risk assessment and recommendations

        Args:
            session: Penetration test session with findings

        Returns:
            Analysis dictionary with risk assessment
        """
        self.logger.info(f"Analyzing findings for session: {session.session_id}")

        context = session.get_context_summary()
        vulnerabilities_summary = session.get_vulnerabilities_summary()

        prompt = f"""Analyze the security findings from this penetration test and provide a comprehensive assessment.

{context}

{vulnerabilities_summary}

Provide a thorough analysis including:
1. Overall risk level (critical/high/medium/low)
2. Most significant vulnerabilities
3. Attack vectors and exploitation paths
4. Potential business impact
5. Prioritized remediation recommendations
6. Quick wins vs long-term fixes

Respond with ONLY valid JSON:
{{
  "overall_risk": "critical/high/medium/low",
  "risk_score": 0.0-10.0,
  "key_vulnerabilities": ["list", "of", "critical", "issues"],
  "attack_vectors": ["possible", "attack", "paths"],
  "business_impact": "Description of potential impact",
  "recommendations": [
    {{
      "priority": "critical/high/medium/low",
      "action": "Specific remediation action",
      "effort": "low/medium/high"
    }}
  ],
  "executive_summary": "2-3 sentence summary for executives"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            self.logger.info(
                f"Analysis complete. Overall risk: {result.get('overall_risk', 'unknown')}"
            )

            # Store conversation
            session.add_conversation_message("user", prompt[:500], module="reasoning")
            session.add_conversation_message("assistant", content, module="reasoning")

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze findings: {e}", exc_info=True)
            return {
                "overall_risk": "unknown",
                "error": str(e)
            }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response
        Handles markdown code blocks and other formatting
        """
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.debug(f"Content: {content}")
            # Try to extract JSON from content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except:
                    pass

            # Return empty result
            return {}

    async def analyze_phase_results(
        self,
        phase: str,
        results: Dict[str, Any],
        session: Session
    ) -> Dict[str, Any]:
        """
        Analyze results from a specific phase execution

        Args:
            phase: Phase name (reconnaissance, enumeration, etc.)
            results: Phase execution results
            session: Session object

        Returns:
            Analysis dictionary with summary, key_findings, recommendations
        """
        self.logger.info(f"Analyzing results for phase: {phase}")

        # Build context from results and session
        vulnerabilities_summary = session.get_vulnerabilities_summary()
        context_summary = session.get_context_summary()

        # Format results for analysis
        results_text = json.dumps(results, indent=2)[:2000]  # Limit size

        prompt = f"""Analyze the results from the {phase} phase of this penetration test.

PHASE: {phase}
TARGET: {session.target}

{context_summary}

{vulnerabilities_summary}

PHASE RESULTS:
{results_text}

Provide a comprehensive analysis:
1. What was accomplished in this phase?
2. What are the key findings?
3. What are the security implications?
4. What should be the next steps?
5. Any concerns or red flags?

Respond with ONLY valid JSON:
{{
  "summary": "1-2 sentence summary of phase results",
  "key_findings": ["finding1", "finding2", "finding3"],
  "vulnerabilities_discovered": 0,
  "assets_discovered": 0,
  "security_implications": "Description of security impact",
  "recommendations": ["recommendation1", "recommendation2"],
  "concerns": ["concern1", "concern2"],
  "next_steps": ["step1", "step2"]
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            result = self._parse_json_response(content)

            self.logger.info(f"Phase analysis complete: {result.get('summary', 'No summary')}")

            # Store conversation
            session.add_conversation_message("user", prompt[:500], module="reasoning")
            session.add_conversation_message("assistant", content, module="reasoning")

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze phase results: {e}", exc_info=True)
            return {
                "summary": f"Phase {phase} completed",
                "key_findings": [],
                "error": str(e)
            }

    def _get_fallback_initial_tasks(self, session: Session) -> List[Task]:
        """Fallback initial tasks if LLM fails"""
        return [
            Task(
                description="Perform comprehensive port scan of target",
                tool="nmap",
                priority=1,
                phase=PentestPhase.RECONNAISSANCE
            ),
            Task(
                description="Identify web technologies and server information",
                tool="nikto",
                priority=2,
                phase=PentestPhase.RECONNAISSANCE
            )
        ]
