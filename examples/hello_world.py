"""
Mnexium SDK - Hello World Example

This example demonstrates the Subject-centric API:
- mnx.subject(id) returns a Subject handle
- subject.create_chat() creates a Chat for multi-turn conversations
- subject.memories, subject.profile, subject.chats for data access

Run with: python hello_world.py
(Requires .env file with OPENAI_API_KEY)
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from mnexium import Mnexium, ProviderConfig, ChatOptions, AuthenticationError


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable is required")
        print("   Add OPENAI_API_KEY=sk-... to your .env file")
        sys.exit(1)

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL") or "https://mnexium.com/api/v1",
        openai=ProviderConfig(api_key=openai_key),
    )

    print("🚀 Mnexium Hello World\n")

    try:
        # Get a Subject handle (no network call)
        alice = mnx.subject()
        print("Subject ID:", alice.id)

        # Create a chat for this subject
        chat = alice.create_chat(ChatOptions(
            model="gpt-4o-mini",
            learn=True,
            history=True,
            recall=True,
        ))
        print("Chat ID:", chat.id)
        print("\n---\n")

        # First message
        response1 = chat.process("Say hello and tell me a fun fact!")
        print("Assistant:", response1.content)

        # Second message — same chat, has history
        print("\n--- Second message (has history) ---\n")
        response2 = chat.process("What did you just tell me?")
        print("Assistant:", response2.content)

        # Third message — learning a preference
        print("\n--- Third message (learning) ---\n")
        response3 = chat.process("My favorite color is blue!")
        print("Assistant:", response3.content)

        # Create a second chat — different chat_id, same subject
        print("\n\n========== CHAT 2 ==========\n")
        chat2 = alice.create_chat(ChatOptions(
            model="gpt-4o-mini",
            learn=True,
            history=True,
            recall=True,
        ))
        print("Chat ID:", chat2.id)
        print("\n---\n")

        response4 = chat2.process("Say hello and tell me a fun fact!")
        print("Assistant:", response4.content)

        print("\n--- Second message (has history) ---\n")
        response5 = chat2.process("What did you just tell me?")
        print("Assistant:", response5.content)

        # Should recall from chat1 that favorite color is blue
        print("\n--- Third message (recall from chat1) ---\n")
        response6 = chat2.process("What is my favorite color?")
        print("Assistant:", response6.content)

        # List chat history for this subject
        print("\n\n========== CHAT HISTORY ==========\n")
        chat_history = alice.chats.list()
        print("Recent chats:", chat_history)

        # Get trial key info
        trial = mnx.get_trial_info()
        if trial:
            print("\n✨ Trial key provisioned!")
            print(trial)

    except AuthenticationError as e:
        print("❌ Authentication failed:", e)


if __name__ == "__main__":
    main()
