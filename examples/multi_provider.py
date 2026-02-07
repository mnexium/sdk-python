"""
Mnexium SDK - Multi-Provider Example

Demonstrates using multiple AI providers with shared memory:
- OpenAI (GPT)
- Anthropic (Claude)
- Google (Gemini)

Memories are shared across all providers.

Run with: python multi_provider.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from mnexium import Mnexium, ProviderConfig, ChatOptions, ChatProcessOptions


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")

    if not openai_key:
        print("❌ OPENAI_API_KEY required in .env")
        sys.exit(1)

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
        anthropic=ProviderConfig(api_key=anthropic_key) if anthropic_key else None,
        google=ProviderConfig(api_key=google_key) if google_key else None,
    )

    print("🔀 Mnexium Multi-Provider Example\n")

    user = mnx.subject("multi-provider-demo")
    chat = user.create_chat(ChatOptions(learn=True, recall=True, history=True))

    # --- OpenAI ---
    print("--- OpenAI (gpt-4o-mini) ---\n")
    r1 = chat.process(ChatProcessOptions(
        content="I love hiking and photography. Remember that!",
        model="gpt-4o-mini",
    ))
    print("GPT:", (r1.content or "")[:150])

    # --- Anthropic (if key available) ---
    if anthropic_key:
        print("\n--- Anthropic (claude-sonnet-4-20250514) ---\n")
        r2 = chat.process(ChatProcessOptions(
            content="What do you know about my hobbies?",
            model="claude-sonnet-4-20250514",
        ))
        print("Claude:", (r2.content or "")[:150])
    else:
        print("\n⏭️  Skipping Anthropic (no ANTHROPIC_API_KEY)")

    # --- Google Gemini (if key available) ---
    if google_key:
        print("\n--- Google (gemini-2.0-flash) ---\n")
        r3 = chat.process(ChatProcessOptions(
            content="Suggest an activity based on what you know about me.",
            model="gemini-2.0-flash",
        ))
        print("Gemini:", (r3.content or "")[:150])
    else:
        print("\n⏭️  Skipping Google (no GOOGLE_API_KEY)")

    # --- Verify cross-provider recall ---
    print("\n--- Cross-provider recall (back to GPT) ---\n")
    r4 = chat.process(ChatProcessOptions(
        content="Summarize everything you know about me.",
        model="gpt-4o-mini",
    ))
    print("GPT:", (r4.content or "")[:200])

    print("\n✅ Multi-provider example complete!")
    print("\nKey takeaway: Memories are shared across all providers.")


if __name__ == "__main__":
    main()
