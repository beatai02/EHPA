"""
Context Manager - Manage conversation context and history
Handles chat memory, session tracking, and context retrieval
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..utils.logger import get_logger


class ContextManager:
    """
    Manages conversation context and history for chatbot interactions

    Responsibilities:
    - Store conversation messages
    - Retrieve relevant context
    - Track session findings
    - Maintain conversation continuity
    """

    def __init__(self, data_dir: str = "./data/chat_history"):
        self.logger = get_logger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for active sessions
        self.conversation_cache: Dict[str, List[Dict[str, Any]]] = {}

        self.logger.info("Context Manager initialized")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation history

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata (intent, entities, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        # Add to cache
        if session_id not in self.conversation_cache:
            self.conversation_cache[session_id] = []

        self.conversation_cache[session_id].append(message)

        # Persist to disk
        self._save_conversation(session_id)

        self.logger.debug(f"Added {role} message to session {session_id}")

    def get_context(
        self,
        session_id: str,
        num_messages: int = 10,
        include_system: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation context

        Args:
            session_id: Session identifier
            num_messages: Number of recent messages to retrieve
            include_system: Whether to include system messages

        Returns:
            List of recent messages
        """
        # Load from cache or disk
        if session_id not in self.conversation_cache:
            self._load_conversation(session_id)

        messages = self.conversation_cache.get(session_id, [])

        # Filter out system messages if requested
        if not include_system:
            messages = [m for m in messages if m["role"] != "system"]

        # Return most recent messages
        return messages[-num_messages:] if messages else []

    def get_full_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full conversation history for a session"""
        if session_id not in self.conversation_cache:
            self._load_conversation(session_id)

        return self.conversation_cache.get(session_id, [])

    def get_conversation_summary(
        self,
        session_id: str,
        max_messages: int = 5
    ) -> str:
        """
        Generate a text summary of recent conversation

        Args:
            session_id: Session identifier
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation summary
        """
        messages = self.get_context(session_id, max_messages)

        if not messages:
            return "No conversation history yet."

        summary_lines = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary_lines.append(f"{role}: {content}")

        return "\n".join(summary_lines)

    def get_relevant_findings(
        self,
        session_id: str,
        session_obj: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Get findings relevant to current conversation

        Args:
            session_id: Session identifier
            session_obj: Optional Session object with findings

        Returns:
            List of relevant findings
        """
        if not session_obj:
            return []

        # Get recent conversation to determine relevance
        recent_messages = self.get_context(session_id, num_messages=3)

        # Extract keywords from recent messages
        keywords = self._extract_keywords(recent_messages)

        # Filter findings based on keywords (simple implementation)
        relevant_findings = []

        # Check vulnerabilities
        for vuln in session_obj.vulnerabilities:
            if self._is_relevant(vuln, keywords):
                relevant_findings.append({
                    "type": "vulnerability",
                    "data": vuln.model_dump()
                })

        # Limit to most recent/relevant
        return relevant_findings[:5]

    def clear_context(self, session_id: str) -> None:
        """Clear conversation context for a session"""
        if session_id in self.conversation_cache:
            del self.conversation_cache[session_id]

        # Optionally delete file
        file_path = self._get_conversation_file(session_id)
        if file_path.exists():
            file_path.unlink()

        self.logger.info(f"Cleared context for session {session_id}")

    def get_context_window(
        self,
        session_id: str,
        max_tokens: int = 4000
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context within token limit

        Args:
            session_id: Session identifier
            max_tokens: Maximum tokens to include (approximate)

        Returns:
            Messages that fit within token limit
        """
        all_messages = self.get_full_conversation(session_id)

        # Estimate tokens (rough: ~4 chars = 1 token)
        token_count = 0
        context_window = []

        # Start from most recent and work backwards
        for message in reversed(all_messages):
            msg_tokens = len(message["content"]) // 4

            if token_count + msg_tokens > max_tokens:
                break

            context_window.insert(0, message)
            token_count += msg_tokens

        return context_window

    def _save_conversation(self, session_id: str) -> None:
        """Save conversation to disk"""
        try:
            file_path = self._get_conversation_file(session_id)

            with open(file_path, 'w') as f:
                json.dump(
                    self.conversation_cache.get(session_id, []),
                    f,
                    indent=2
                )
        except Exception as e:
            self.logger.error(f"Failed to save conversation: {e}")

    def _load_conversation(self, session_id: str) -> None:
        """Load conversation from disk"""
        try:
            file_path = self._get_conversation_file(session_id)

            if file_path.exists():
                with open(file_path, 'r') as f:
                    self.conversation_cache[session_id] = json.load(f)
            else:
                self.conversation_cache[session_id] = []
        except Exception as e:
            self.logger.error(f"Failed to load conversation: {e}")
            self.conversation_cache[session_id] = []

    def _get_conversation_file(self, session_id: str) -> Path:
        """Get file path for conversation storage"""
        return self.data_dir / f"{session_id}_chat.json"

    def _extract_keywords(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from messages (simple implementation)"""
        keywords = []

        # Common security terms
        security_terms = [
            'sql', 'injection', 'xss', 'rce', 'csrf', 'xxe', 'ssrf',
            'vulnerability', 'exploit', 'critical', 'high', 'medium', 'low',
            'port', 'service', 'version', 'cve'
        ]

        for msg in messages:
            content = msg["content"].lower()
            for term in security_terms:
                if term in content:
                    keywords.append(term)

        return list(set(keywords))

    def _is_relevant(self, item: Any, keywords: List[str]) -> bool:
        """Check if an item is relevant based on keywords"""
        if not keywords:
            return True  # If no keywords, consider everything relevant

        # Convert item to string and check for keywords
        item_str = str(item).lower()

        for keyword in keywords:
            if keyword in item_str:
                return True

        return False

    def get_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get conversation statistics"""
        messages = self.get_full_conversation(session_id)

        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]

        return {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "conversation_duration": self._calculate_duration(messages),
            "first_message": messages[0]["timestamp"] if messages else None,
            "last_message": messages[-1]["timestamp"] if messages else None
        }

    def _calculate_duration(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Calculate conversation duration"""
        if len(messages) < 2:
            return None

        try:
            first = datetime.fromisoformat(messages[0]["timestamp"])
            last = datetime.fromisoformat(messages[-1]["timestamp"])
            duration = last - first

            minutes = int(duration.total_seconds() / 60)
            return f"{minutes} minutes"
        except:
            return None
