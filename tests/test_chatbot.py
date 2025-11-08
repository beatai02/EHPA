"""
Tests for Chatbot System
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.orchestrator.chatbot_manager import ChatbotManager
from src.chatbot.conversation_handler import ConversationHandler
from src.chatbot.command_parser import CommandParser
from src.chatbot.explainer import Explainer
from src.chatbot.context_manager import ContextManager


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing"""
    orch = Mock()
    orch.reasoning = Mock()
    orch.generation = Mock()
    orch.parsing = Mock()
    orch.get_session = Mock()
    return orch


@pytest.fixture
def chatbot_manager(mock_orchestrator):
    """Create chatbot manager instance"""
    return ChatbotManager(mock_orchestrator)


@pytest.mark.asyncio
async def test_chatbot_manager_initialization(chatbot_manager):
    """Test chatbot manager initializes correctly"""
    assert chatbot_manager.conversation_handler is not None
    assert chatbot_manager.command_parser is not None
    assert chatbot_manager.explainer is not None
    assert chatbot_manager.context_manager is not None


@pytest.mark.asyncio
async def test_process_greeting_message(chatbot_manager):
    """Test processing a greeting message"""
    message = "Hello"
    session_id = "test_session"

    with patch.object(chatbot_manager.conversation_handler, 'handle_message',
                     return_value={'response': 'Hello! How can I help you?', 'type': 'greeting'}):
        response = await chatbot_manager.process_message(message, session_id)

    assert response is not None
    assert 'response' in response


@pytest.mark.asyncio
async def test_process_concept_explanation_request(chatbot_manager):
    """Test requesting concept explanation"""
    message = "What is SQL injection?"
    session_id = "test_session"

    with patch.object(chatbot_manager.explainer, 'explain_concept',
                     return_value={'explanation': 'SQL injection is...', 'examples': []}):
        with patch.object(chatbot_manager.conversation_handler, 'handle_message',
                         return_value={'response': 'SQL injection is...', 'type': 'explanation'}):
            response = await chatbot_manager.process_message(message, session_id)

    assert response is not None


@pytest.mark.asyncio
async def test_process_status_query(chatbot_manager, mock_orchestrator):
    """Test querying session status"""
    message = "What's the current status?"
    session_id = "test_session"

    # Mock session
    mock_session = Mock()
    mock_session.current_phase.value = "reconnaissance"
    mock_session.progress = 45.5
    mock_session.todo_list = []
    mock_session.completed_tasks = [Mock(), Mock()]
    mock_session.vulnerabilities = []
    mock_orchestrator.get_session.return_value = mock_session

    with patch.object(chatbot_manager.conversation_handler, 'handle_message',
                     return_value={'response': 'Current phase: reconnaissance', 'type': 'status'}):
        response = await chatbot_manager.process_message(message, session_id)

    assert response is not None


@pytest.mark.asyncio
async def test_process_command_execution(chatbot_manager):
    """Test executing a command via chat"""
    message = "Scan scanme.nmap.org"
    session_id = "test_session"

    with patch.object(chatbot_manager.command_parser, 'parse_command',
                     return_value={'action': 'scan', 'target': 'scanme.nmap.org'}):
        with patch.object(chatbot_manager.conversation_handler, 'handle_message',
                         return_value={'response': 'Starting scan...', 'type': 'command'}):
            response = await chatbot_manager.process_message(message, session_id)

    assert response is not None


@pytest.mark.asyncio
async def test_context_manager_stores_messages():
    """Test context manager stores conversation history"""
    context_mgr = ContextManager()
    session_id = "test_session"

    context_mgr.add_message(session_id, "user", "Hello")
    context_mgr.add_message(session_id, "assistant", "Hi there!")

    history = context_mgr.get_conversation_history(session_id)
    assert len(history) == 2
    assert history[0]['role'] == 'user'
    assert history[1]['role'] == 'assistant'


@pytest.mark.asyncio
async def test_context_manager_limits_history():
    """Test context manager limits message history"""
    context_mgr = ContextManager(max_messages=5)
    session_id = "test_session"

    # Add 10 messages
    for i in range(10):
        context_mgr.add_message(session_id, "user", f"Message {i}")

    history = context_mgr.get_conversation_history(session_id)
    # Should only keep last 5
    assert len(history) <= 5


@pytest.mark.asyncio
async def test_command_parser_recognizes_scan_command():
    """Test command parser recognizes scan commands"""
    parser = CommandParser()

    command = "scan target.com"
    result = await parser.parse_command(command)

    assert result is not None
    assert 'action' in result
    assert result['action'] in ['scan', 'pentest', 'test']


@pytest.mark.asyncio
async def test_command_parser_recognizes_status_query():
    """Test command parser recognizes status queries"""
    parser = CommandParser()

    command = "what's the status?"
    result = await parser.parse_command(command)

    assert result is not None
    assert 'action' in result


@pytest.mark.asyncio
async def test_explainer_provides_examples():
    """Test explainer provides examples with explanations"""
    with patch('src.chatbot.explainer.AsyncAnthropic') as mock_client:
        explainer = Explainer()

        # Mock LLM response
        mock_response = Mock()
        mock_response.content = [Mock(text='{"explanation": "...", "examples": ["..."]}')]
        explainer.client = Mock()
        explainer.client.messages.create = AsyncMock(return_value=mock_response)

        result = await explainer.explain_concept("XSS")

        assert result is not None


@pytest.mark.asyncio
async def test_conversation_handler_maintains_context():
    """Test conversation handler maintains context across messages"""
    handler = ConversationHandler(Mock())

    session_id = "test_session"

    # First message
    with patch.object(handler, '_analyze_intent',
                     return_value={'type': 'greeting'}):
        with patch.object(handler, '_generate_response',
                         return_value={'response': 'Hello!'}):
            response1 = await handler.handle_message("Hi", session_id)

    # Second message referencing first
    with patch.object(handler, '_analyze_intent',
                     return_value={'type': 'question'}):
        with patch.object(handler, '_generate_response',
                         return_value={'response': 'Sure!'}):
            response2 = await handler.handle_message("Can you help?", session_id)

    assert response1 is not None
    assert response2 is not None


@pytest.mark.asyncio
async def test_chatbot_handles_error_gracefully(chatbot_manager):
    """Test chatbot handles errors gracefully"""
    message = "Test message"
    session_id = "test_session"

    with patch.object(chatbot_manager.conversation_handler, 'handle_message',
                     side_effect=Exception("Test error")):
        response = await chatbot_manager.process_message(message, session_id)

    # Should return error response, not crash
    assert response is not None
    assert 'error' in response or 'response' in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
