"""
Conversation Handler - Main chatbot conversation logic
Coordinates all chatbot components to handle user messages
"""

import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from anthropic import AsyncAnthropic
import json

from .context_manager import ContextManager
from .command_parser import CommandParser, ParsedCommand
from .explainer import Explainer
from .response_generator import ResponseGenerator
from ..core.config import config
from ..utils.logger import get_logger


class ConversationHandler:
    """
    Main conversation handler that processes user messages

    Workflow:
    1. Receive user message
    2. Analyze intent using LLM
    3. Route to appropriate handler (command, question, explanation)
    4. Generate response
    5. Update context
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # Initialize components
        self.context_manager = ContextManager()
        self.command_parser = CommandParser()
        self.explainer = Explainer()
        self.response_generator = ResponseGenerator()

        # LLM client for intent analysis
        self.client = AsyncAnthropic(api_key=config.settings.anthropic_api_key)
        self.model = config.llm.model

        # Load prompts
        prompts_path = Path("./configs/chatbot_prompts.yaml")
        with open(prompts_path, 'r') as f:
            prompts_config = yaml.safe_load(f)
            self.base_prompt = prompts_config['system_prompts']['base']
            self.intent_classifier_prompt = prompts_config['system_prompts']['intent_classifier']
            self.conversation_patterns = prompts_config.get('conversation_patterns', {})

        self.logger.info("Conversation Handler initialized")

    async def handle_message(
        self,
        message: str,
        session_id: str,
        user_id: str = "default_user",
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate response

        Args:
            message: User's message
            session_id: Session identifier
            user_id: User identifier
            session_obj: Optional Session object for context

        Returns:
            Response dictionary with message, type, data, and suggestions
        """
        self.logger.info(f"Handling message for session {session_id}: {message[:50]}...")

        try:
            # Add user message to context
            self.context_manager.add_message(
                session_id=session_id,
                role="user",
                content=message
            )

            # Check for pattern matches first (greetings, help, etc.)
            pattern_response = self._check_patterns(message)
            if pattern_response:
                self._add_response_to_context(session_id, pattern_response)
                return pattern_response

            # Analyze intent
            intent = await self._analyze_intent(message, session_id, session_obj)

            # Route based on intent type
            if intent['type'] == 'command':
                response = await self._handle_command(intent, session_id, session_obj)
            elif intent['type'] == 'explanation':
                response = await self._handle_explanation(intent, session_id, session_obj)
            elif intent['type'] == 'question':
                response = await self._handle_question(intent, session_id, session_obj)
            elif intent['type'] == 'guidance':
                response = await self._handle_guidance(intent, session_id, session_obj)
            else:
                response = await self._handle_general(intent, session_id, session_obj)

            # Add response to context
            self._add_response_to_context(session_id, response)

            return response

        except Exception as e:
            self.logger.error(f"Error handling message: {e}", exc_info=True)
            error_response = self.response_generator.format_error(
                error_message=str(e),
                explanation="I encountered an error processing your request.",
                suggestions=["Try rephrasing", "Start a new conversation", "Contact support"]
            )
            self._add_response_to_context(session_id, error_response)
            return error_response

    async def _analyze_intent(
        self,
        message: str,
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """
        Analyze user intent using LLM

        Returns:
            Intent dictionary with type and extracted entities
        """
        # Get conversation context
        context = self.context_manager.get_context(session_id, num_messages=5)

        # Build context summary
        context_summary = ""
        if session_obj:
            context_summary = f"""
Current session state:
- Target: {session_obj.target}
- Phase: {session_obj.current_phase.value}
- Progress: {session_obj.progress}%
- Vulnerabilities found: {len(session_obj.vulnerabilities)}
"""

        prompt = f"""Analyze this user message and classify the intent.

User message: "{message}"

{context_summary}

Recent conversation:
{self._format_context(context[-3:])}

Classify into one of these intent types:
1. COMMAND - Execute security testing action (scan, run tool, test vulnerability)
2. QUESTION - Ask about current state/progress (status, results, findings)
3. EXPLANATION - Learn about security concept (what is XSS, how does nmap work)
4. GUIDANCE - Request recommendations (what next, prioritize, suggest)
5. GENERAL - Other (greetings, thanks, clarifications)

Extract entities:
- target: Domain/IP if mentioned
- tool: Security tool if mentioned
- concept: Security concept if asking for explanation
- action: Specific action requested

Respond ONLY with valid JSON in this exact format:
{{
  "type": "command|question|explanation|guidance|general",
  "confidence": 0.0-1.0,
  "entities": {{
    "target": "domain or IP or null",
    "tool": "tool name or null",
    "concept": "concept name or null",
    "action": "action name or null"
  }},
  "summary": "brief summary of intent"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=0.3,  # Lower temperature for classification
                system=self.intent_classifier_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            intent = self._parse_json_response(content)

            self.logger.debug(f"Intent analysis: {intent.get('type')} (confidence: {intent.get('confidence')})")

            return intent

        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            # Fallback to command parser
            parsed_command = self.command_parser.parse(message)
            return {
                'type': 'command' if parsed_command.action != 'unknown' else 'general',
                'confidence': parsed_command.confidence,
                'entities': {
                    'target': parsed_command.target,
                    'tool': parsed_command.tool,
                    'action': parsed_command.action
                },
                'summary': 'Fallback parsing'
            }

    async def _handle_command(
        self,
        intent: Dict[str, Any],
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """Handle command execution intent"""
        entities = intent.get('entities', {})
        action = entities.get('action', 'unknown')

        # Return command intent for orchestrator to execute
        return {
            'message': f"I understand you want to: {intent.get('summary', 'execute a command')}\n\nI'll proceed with this action.",
            'type': 'command_intent',
            'data': {
                'intent': intent,
                'entities': entities,
                'requires_execution': True
            },
            'suggestions': [
                "Explain what this will do",
                "Show me the command",
                "Cancel"
            ]
        }

    async def _handle_explanation(
        self,
        intent: Dict[str, Any],
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """Handle explanation request"""
        entities = intent.get('entities', {})
        concept = entities.get('concept', '')

        if not concept:
            return {
                'message': "What would you like me to explain? You can ask about vulnerabilities (SQL injection, XSS), tools (nmap, metasploit), or phases (reconnaissance, exploitation).",
                'type': 'clarification',
                'data': {},
                'suggestions': [
                    "Explain SQL injection",
                    "How does nmap work?",
                    "What is reconnaissance?"
                ]
            }

        # Generate explanation
        context_data = None
        if session_obj:
            context_data = {
                'phase': session_obj.current_phase.value,
                'target': session_obj.target,
                'vulnerabilities': [v.model_dump() for v in session_obj.vulnerabilities]
            }

        explanation = await self.explainer.explain(
            topic=concept,
            user_level="intermediate",
            context=context_data
        )

        # Get quick tip if available
        tip = self.explainer.get_quick_tip(concept)
        if tip:
            explanation += f"\n\n{tip}"

        return {
            'message': explanation,
            'type': 'explanation',
            'data': {'concept': concept},
            'suggestions': [
                f"Test for {concept}"if 'injection' in concept.lower() or 'xss' in concept.lower() else "Learn more",
                "Show related findings",
                "What else can you explain?"
            ]
        }

    async def _handle_question(
        self,
        intent: Dict[str, Any],
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """Handle status/progress questions"""
        if not session_obj:
            return {
                'message': "No active penetration test session. Start a scan first!",
                'type': 'info',
                'data': {},
                'suggestions': [
                    "Start a scan",
                    "How do I begin?",
                    "Help"
                ]
            }

        # Generate status summary
        session_data = {
            'target': session_obj.target,
            'phase': session_obj.current_phase.value.replace('_', ' ').title(),
            'progress': session_obj.progress,
            'critical_count': len([v for v in session_obj.vulnerabilities if v.severity.value == 'critical']),
            'high_count': len([v for v in session_obj.vulnerabilities if v.severity.value == 'high']),
            'medium_count': len([v for v in session_obj.vulnerabilities if v.severity.value == 'medium']),
            'low_count': len([v for v in session_obj.vulnerabilities if v.severity.value == 'low']),
            'info_count': len([v for v in session_obj.vulnerabilities if v.severity.value == 'informational']),
            'vulnerabilities': [v.model_dump() for v in session_obj.vulnerabilities]
        }

        return self.response_generator.format_results_summary(session_data)

    async def _handle_guidance(
        self,
        intent: Dict[str, Any],
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """Handle guidance/recommendation requests"""
        if not session_obj:
            return {
                'message': """**Getting Started with EHPA:**

1. **Start a scan**: Tell me a target to scan (e.g., "scan scanme.nmap.org")
2. **Learn**: Ask me to explain security concepts
3. **Monitor**: Check progress with "show status"
4. **Review**: Get findings with "show results"

What would you like to do first?""",
                'type': 'guidance',
                'data': {},
                'suggestions': [
                    "Scan scanme.nmap.org",
                    "Explain reconnaissance",
                    "What tools do you have?"
                ]
            }

        # Generate recommendations based on current state
        phase = session_obj.current_phase.value
        vuln_count = len(session_obj.vulnerabilities)
        progress = session_obj.progress

        recommendations = []

        if progress < 30:
            recommendations.append("Continue reconnaissance to discover more about the target")
        elif progress < 60:
            recommendations.append("Focus on vulnerability scanning for the discovered services")
        elif vuln_count > 0:
            recommendations.append(f"You have {vuln_count} vulnerabilities - prioritize critical/high severity")
            recommendations.append("Consider moving to exploitation phase (with approval)")
        else:
            recommendations.append("No major vulnerabilities found - comprehensive manual testing recommended")

        recommendations.append("Generate report to document findings")


        message = f"""**Recommendations for {session_obj.target}:**

Current Phase: {phase.replace('_', ' ').title()} ({progress}% complete)

{chr(10).join(recommendations)}

What would you like to do?"""

        return {
            'message': message,
            'type': 'guidance',
            'data': {'phase': phase, 'progress': progress},
            'suggestions': [
                "Continue current phase",
                "Show vulnerabilities",
                "Generate report",
                "Explain next steps"
            ]
        }

    async def _handle_general(
        self,
        intent: Dict[str, Any],
        session_id: str,
        session_obj: Any = None
    ) -> Dict[str, Any]:
        """Handle general conversation"""
        # Use LLM for general conversation
        context = self.context_manager.get_context(session_id, num_messages=5)

        prompt = f"""Have a helpful conversation with the user about penetration testing.

Recent conversation:
{self._format_context(context)}

User's latest message expresses: {intent.get('summary', 'general inquiry')}

Respond in a friendly, professional way. Keep it concise (2-3 sentences).
If appropriate, guide them towards using EHPA's capabilities."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=256,
                temperature=0.7,
                system=self.base_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            message = response.content[0].text

            return {
                'message': message,
                'type': 'general',
                'data': {},
                'suggestions': self.response_generator.generate_suggestions('general')
            }

        except Exception as e:
            self.logger.error(f"General conversation failed: {e}")
            return self.response_generator.format_help()

    def _check_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """Check for predefined conversation patterns"""
        message_lower = message.lower().strip()

        # Greetings
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
            return self.response_generator.format_greeting()

        # Help
        if any(help_word in message_lower for help_word in ['help', 'what can you do', 'capabilities']):
            return self.response_generator.format_help()

        return None

    def _format_context(self, messages: list) -> str:
        """Format conversation context for prompts"""
        formatted = []
        for msg in messages:
            role = msg['role'].capitalize()
            content = msg['content'][:100] + "..."if len(msg['content']) > 100 else msg['content']
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted) if formatted else "No previous context"

    def _add_response_to_context(self, session_id: str, response: Dict[str, Any]) -> None:
        """Add bot response to conversation context"""
        self.context_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=response['message'],
            metadata={
                'type': response.get('type'),
                'data': response.get('data', {})
            }
        )

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        content = content.strip()

        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except:
                    pass

        # Return default
        return {
            'type': 'general',
            'confidence': 0.3,
            'entities': {},
            'summary': 'Unable to parse intent'
        }
