#!/usr/bin/env python3
"""
EHPA Chatbot Demo
Demonstrates interactive chatbot capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import Orchestrator
from src.orchestrator.chatbot_manager import ChatbotManager


async def main():
    """
    Interactive chatbot demo
    """
    print("="*70)
    print("  EHPA - AI Chatbot Demo")
    print("  Type 'help' for commands, 'quit' to exit")
    print("="*70)

    # Initialize orchestrator
    orchestrator = Orchestrator()
    chatbot = orchestrator.chatbot_manager

    # Create a test session
    session_id = "demo_session"

    print("\n🤖 EHPA Chatbot is ready!")
    print("   You can:")
    print("   - Ask security questions (e.g., 'What is XSS?')")
    print("   - Request scans (e.g., 'Scan scanme.nmap.org')")
    print("   - Check status (e.g., 'What's the status?')")
    print("   - Get explanations (e.g., 'Explain SQL injection')")
    print()

    # Example conversations
    example_messages = [
        "Hello!",
        "What is SQL injection?",
        "How does nmap work?",
        "What are the phases of a penetration test?",
    ]

    print("📝 Running example conversations...\n")

    for i, message in enumerate(example_messages, 1):
        print(f"\n{'─'*70}")
        print(f"[{i}/{len(example_messages)}] User: {message}")
        print(f"{'─'*70}")

        try:
            # Process message through chatbot
            response = await chatbot.process_message(message, session_id)

            # Display response
            if isinstance(response, dict):
                if 'response' in response:
                    print(f"\n🤖 EHPA: {response['response']}")
                elif 'text' in response:
                    print(f"\n🤖 EHPA: {response['text']}")
                else:
                    print(f"\n🤖 EHPA: {response}")

                # Show additional info if available
                if 'type' in response:
                    print(f"   (Type: {response['type']})")
            else:
                print(f"\n🤖 EHPA: {response}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

        # Small delay between messages
        await asyncio.sleep(1)

    # Interactive mode
    print("\n" + "="*70)
    print("🎮 Interactive Mode - Now you can chat!")
    print("   Type your questions or commands...")
    print("   Commands: 'help', 'history', 'clear', 'quit'")
    print("="*70)

    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == 'quit':
                print("\n👋 Goodbye!")
                break

            elif user_input.lower() == 'help':
                print("\n📚 Available Commands:")
                print("   help     - Show this help message")
                print("   history  - Show conversation history")
                print("   clear    - Clear conversation history")
                print("   quit     - Exit chatbot")
                print("\n💡 Example Questions:")
                print("   - What is XSS?")
                print("   - Explain SQL injection with examples")
                print("   - How do I find hidden directories?")
                print("   - What tools are used for OSINT?")
                continue

            elif user_input.lower() == 'history':
                history = chatbot.context_manager.get_conversation_history(session_id)
                print(f"\n📜 Conversation History ({len(history)} messages):")
                for msg in history[-10:]:  # Last 10 messages
                    role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                    content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                    print(f"   {role_emoji} {content}")
                continue

            elif user_input.lower() == 'clear':
                chatbot.context_manager.clear_history(session_id)
                print("\n🗑️  Conversation history cleared")
                continue

            # Process message
            print("\n🤖 EHPA: ", end="", flush=True)

            response = await chatbot.process_message(user_input, session_id)

            # Display response
            if isinstance(response, dict):
                if 'response' in response:
                    print(response['response'])
                elif 'text' in response:
                    print(response['text'])
                else:
                    print(response)
            else:
                print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 EOF. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Cleanup
    await orchestrator.cleanup()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Goodbye!")
        sys.exit(0)
