"""
Mnexium SDK - Streaming Example

Demonstrates real-time streaming responses:
1. Create a chat with streaming enabled
2. Iterate over chunks as they arrive
3. Access metadata after stream completes

Run with: python streaming.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from mnexium import Mnexium, ProviderConfig, ChatOptions, ChatProcessOptions


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY required in .env")
        sys.exit(1)

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
    )

    print("🌊 Mnexium Streaming Example\n")

    user = mnx.subject("streaming-demo")
    chat = user.create_chat(ChatOptions(
        model="gpt-4o-mini",
        learn=True,
        history=True,
    ))

    # --- Streaming with iteration ---
    print("--- Streaming response ---\n")

    stream = chat.process(ChatProcessOptions(
        content="Tell me a short story about a robot learning to paint. Keep it under 100 words.",
        stream=True,
    ))

    for chunk in stream:
        print(chunk.content, end="", flush=True)

    print("\n")

    # Metadata available after stream completes
    print("--- Stream metadata ---")
    print(f"Chat ID: {stream.chat_id}")
    print(f"Total length: {len(stream.total_content)} chars")
    if stream.usage:
        print(f"Usage: {stream.usage.prompt_tokens} prompt + {stream.usage.completion_tokens} completion = {stream.usage.total_tokens} total")

    # --- Collect full text at once ---
    print("\n--- Collecting full text ---\n")

    stream2 = chat.process(ChatProcessOptions(
        content="Now summarize that story in one sentence.",
        stream=True,
    ))
    text = stream2.text()
    print("Summary:", text)

    print("\n✅ Streaming example complete!")


if __name__ == "__main__":
    main()
