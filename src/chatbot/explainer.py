"""
Explainer - Educational content generation
Provides explanations for security concepts, vulnerabilities, and tools
"""

import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from anthropic import AsyncAnthropic

from ..core.config import config
from ..utils.logger import get_logger


class Explainer:
    """
    Provide educational explanations for security concepts

    Responsibilities:
    - Explain vulnerabilities (SQL injection, XSS, etc.)
    - Explain tools (nmap, metasploit, etc.)
    - Explain phases and methodologies
    - Adapt explanations to user level
    - Relate explanations to current findings
    """

    def __init__(self, educational_content_path: str = "./configs/educational_content.yaml"):
        self.logger = get_logger(__name__)
        self.client = AsyncAnthropic(api_key=config.settings.anthropic_api_key)
        self.model = config.llm.model

        # Load educational content database
        self.content_db = self._load_educational_content(educational_content_path)

        # Load prompts
        prompts_path = Path("./configs/chatbot_prompts.yaml")
        with open(prompts_path, 'r') as f:
            prompts_config = yaml.safe_load(f)
            self.system_prompt = prompts_config['system_prompts']['explainer']

        self.logger.info("Explainer initialized")

    def _load_educational_content(self, path: str) -> Dict[str, Any]:
        """Load educational content from YAML file"""
        try:
            content_path = Path(path)
            if content_path.exists():
                with open(content_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning(f"Educational content file not found: {path}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load educational content: {e}")
            return {}

    async def explain(
        self,
        topic: str,
        user_level: str = "intermediate",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate explanation for a security topic

        Args:
            topic: Topic to explain (e.g., "SQL injection", "nmap", "reconnaissance")
            user_level: User expertise level (beginner, intermediate, advanced)
            context: Optional context from current session

        Returns:
            Educational explanation text
        """
        self.logger.info(f"Explaining topic: {topic} (level: {user_level})")

        # Normalize topic
        topic_normalized = topic.lower().strip()

        # Check if we have pre-defined content
        static_explanation = self._get_static_explanation(topic_normalized, user_level)

        if static_explanation:
            # Enhance with LLM if context is available
            if context:
                return await self._enhance_with_context(
                    static_explanation,
                    topic_normalized,
                    context
                )
            return static_explanation

        # Generate explanation using LLM
        return await self._generate_explanation_llm(topic, user_level, context)

    def _get_static_explanation(self, topic: str, level: str) -> Optional[str]:
        """Get pre-defined explanation from content database"""
        # Check vulnerabilities
        if 'vulnerabilities' in self.content_db:
            for vuln_key, vuln_data in self.content_db['vulnerabilities'].items():
                if vuln_key in topic or vuln_data['name'].lower() in topic:
                    return self._format_vulnerability_explanation(vuln_data, level)

        # Check tools
        if 'tools' in self.content_db:
            for tool_key, tool_data in self.content_db['tools'].items():
                if tool_key in topic:
                    return self._format_tool_explanation(tool_data)

        # Check phases
        if 'phases' in self.content_db:
            for phase_key, phase_data in self.content_db['phases'].items():
                if phase_key in topic:
                    return self._format_phase_explanation(phase_data)

        return None

    def _format_vulnerability_explanation(
        self,
        vuln_data: Dict[str, Any],
        level: str
    ) -> str:
        """Format vulnerability explanation"""
        explanation_parts = []

        # Title
        explanation_parts.append(f"**{vuln_data['name']}**")
        explanation_parts.append(f"Category: {vuln_data['category']} | Severity: {vuln_data['severity']}")
        explanation_parts.append("")

        # Main explanation based on level
        if 'simple_explanation' in vuln_data and level == "beginner":
            explanation_parts.append(vuln_data['simple_explanation'])
        elif 'technical_details' in vuln_data:
            explanation_parts.append(vuln_data['technical_details'])

        # Add real-world examples
        if 'real_world_examples' in vuln_data:
            explanation_parts.append("\n**Real-World Examples:**")
            for example in vuln_data['real_world_examples']:
                explanation_parts.append(f"- {example}")

        # Add detection methods
        if 'detection_methods' in vuln_data:
            explanation_parts.append("\n**How to Detect:**")
            for method in vuln_data['detection_methods']:
                explanation_parts.append(f"- {method}")

        # Add remediation
        if 'remediation' in vuln_data:
            explanation_parts.append("\n**How to Fix:**")
            for fix in vuln_data['remediation']:
                explanation_parts.append(f"- {fix}")

        return "\n".join(explanation_parts)

    def _format_tool_explanation(self, tool_data: Dict[str, Any]) -> str:
        """Format tool explanation"""
        explanation_parts = []

        # Title
        explanation_parts.append(f"**{tool_data['name']}**")
        explanation_parts.append(f"Category: {tool_data['category']}")
        explanation_parts.append("")

        # Description
        if 'description' in tool_data:
            explanation_parts.append(tool_data['description'])

        # Common commands
        if 'common_commands' in tool_data:
            explanation_parts.append("\n**Common Commands:**")
            for cmd in tool_data['common_commands']:
                explanation_parts.append(f"```\n{cmd['command']}\n```")
                explanation_parts.append(f"*{cmd['description']}*\n")

        # Workflow
        if 'workflow' in tool_data:
            explanation_parts.append("\n**Typical Workflow:**")
            for step in tool_data['workflow']:
                explanation_parts.append(f"{step['step']}. {step['action']}")
                if 'command' in step:
                    explanation_parts.append(f"   `{step['command']}`")

        # Best practices
        if 'best_practices' in tool_data:
            explanation_parts.append("\n**Best Practices:**")
            for practice in tool_data['best_practices']:
                explanation_parts.append(f"- {practice}")

        return "\n".join(explanation_parts)

    def _format_phase_explanation(self, phase_data: Dict[str, Any]) -> str:
        """Format phase explanation"""
        explanation_parts = []

        # Title
        explanation_parts.append(f"**{phase_data['name']} Phase**")
        explanation_parts.append(f"Order: Phase {phase_data['order']}")
        explanation_parts.append("")

        # Purpose
        if 'purpose' in phase_data:
            explanation_parts.append("**Purpose:**")
            explanation_parts.append(phase_data['purpose'])
            explanation_parts.append("")

        # Activities
        if 'activities' in phase_data:
            explanation_parts.append("**Key Activities:**")
            for activity in phase_data['activities']:
                explanation_parts.append(f"- {activity}")
            explanation_parts.append("")

        # Tools
        if 'tools' in phase_data:
            explanation_parts.append("**Common Tools:**")
            for tool in phase_data['tools']:
                if isinstance(tool, dict):
                    explanation_parts.append(f"- **{tool['name']}**: {tool['purpose']}")
                else:
                    explanation_parts.append(f"- {tool}")
            explanation_parts.append("")

        # Success criteria
        if 'success_criteria' in phase_data:
            explanation_parts.append("**Success Criteria:**")
            for criteria in phase_data['success_criteria']:
                explanation_parts.append(f" {criteria}")

        # Warnings
        if 'warnings' in phase_data:
            explanation_parts.append("\n**  Important Warnings:**")
            for warning in phase_data['warnings']:
                explanation_parts.append(warning)

        return "\n".join(explanation_parts)

    async def _generate_explanation_llm(
        self,
        topic: str,
        user_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate explanation using LLM"""
        prompt = f"""Explain the following cybersecurity topic: "{topic}"

User expertise level: {user_level}

Provide a clear, educational explanation that:
1. Starts with a simple analogy or definition
2. Provides technical details appropriate for {user_level} level
3. Includes real-world examples when relevant
4. Explains practical implications

"""

        if context:
            prompt += f"\nCurrent testing context: {context.get('phase', 'N/A')} phase"
            if context.get('findings'):
                prompt += f"\nRelate explanation to current findings when relevant."

        prompt += "\n\nProvide the explanation in markdown format."

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Failed to generate explanation: {e}")
            return f"I apologize, but I encountered an error while explaining {topic}. Please try rephrasing your question."

    async def _enhance_with_context(
        self,
        base_explanation: str,
        topic: str,
        context: Dict[str, Any]
    ) -> str:
        """Enhance static explanation with current session context"""
        prompt = f"""You are providing an explanation about "{topic}".

Base explanation:
{base_explanation}

Current penetration test context:
- Phase: {context.get('phase', 'N/A')}
- Target: {context.get('target', 'N/A')}
- Findings so far: {len(context.get('vulnerabilities', []))} vulnerabilities discovered

Enhance the base explanation by:
1. Relating it to the current testing context
2. Mentioning if we've found related issues
3. Suggesting next steps relevant to this topic

Keep the enhanced explanation concise (add 2-3 sentences max).
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=0.7,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            enhancement = response.content[0].text
            return f"{base_explanation}\n\n**In Your Current Test:**\n{enhancement}"

        except Exception as e:
            self.logger.error(f"Failed to enhance explanation: {e}")
            return base_explanation

    def get_quick_tip(self, topic: str) -> str:
        """Get a quick tip or one-liner about a topic"""
        tips = {
            'sql_injection': "Always use parameterized queries - never concatenate user input into SQL!",
            'xss': "Encode all user output - what goes in may come out dangerous!",
            'nmap': "Start with -sV -sC for service detection and safe scripts.",
            'metasploit': "Always run 'check' before 'exploit' to avoid crashes.",
            'reconnaissance': "More time in recon = less time stuck later.",
            'enumeration': "Enumerate everything - hidden directories often hold treasures.",
        }

        topic_normalized = topic.lower().strip()
        for key, tip in tips.items():
            if key in topic_normalized:
                return f"=  Quick Tip: {tip}"

        return ""

    def list_available_topics(self) -> Dict[str, List[str]]:
        """List all topics available for explanation"""
        available_topics = {
            'vulnerabilities': [],
            'tools': [],
            'phases': []
        }

        if 'vulnerabilities' in self.content_db:
            available_topics['vulnerabilities'] = [
                v['name'] for v in self.content_db['vulnerabilities'].values()
            ]

        if 'tools' in self.content_db:
            available_topics['tools'] = [
                t['name'] for t in self.content_db['tools'].values()
            ]

        if 'phases' in self.content_db:
            available_topics['phases'] = [
                p['name'] for p in self.content_db['phases'].values()
            ]

        return available_topics
