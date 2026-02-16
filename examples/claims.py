"""
Mnexium SDK - Claims Example

Demonstrates structured claims (facts) about a subject:
- Set claims with confidence scores
- Get claims by slot
- List all claim slots
- Get current truth
- Retract claims

Run with: python claims.py
"""

import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

from mnexium import Mnexium, ProviderConfig, ChatOptions


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("⏭️  Skipping: OPENAI_API_KEY not set")
        return

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
    )

    print("📋 Mnexium Claims Example\n")

    user = mnx.subject("claims-demo")

    # --- Set claims manually ---
    print("--- Setting claims ---\n")

    user.claims.set("favorite_color", "blue", confidence=0.95)
    print("Set: favorite_color = blue (0.95)")

    user.claims.set("location", "San Francisco", confidence=0.9)
    print("Set: location = San Francisco (0.9)")

    user.claims.set("occupation", "software engineer", confidence=0.85)
    print("Set: occupation = software engineer (0.85)")

    # --- Get a specific claim ---
    print("\n--- Get specific claim ---\n")

    color = user.claims.get("favorite_color")
    print("favorite_color:", color)

    # --- List all slots ---
    print("\n--- List all slots ---\n")

    slots = user.claims.list()
    print("Slots:", slots)

    # --- Get current truth ---
    print("\n--- Current truth ---\n")

    truth = user.claims.truth()
    print("Truth:", truth)

    # --- Claim history ---
    print("\n--- Claim history ---\n")

    history = user.claims.history()
    print(f"History entries: {len(history)}")
    for h in history[:5]:
        print(f"  - {h}")

    # --- Extract claims via chat ---
    print("\n--- Extract claims via chat (learn=True) ---\n")

    chat = user.create_chat(ChatOptions(
        model="gpt-4o-mini",
        learn=True,
    ))
    response = chat.process("I'm 28 years old and I love playing guitar.")
    print("AI:", (response.content or "")[:100])

    # Check if new claims were extracted
    import time
    time.sleep(2)  # Wait for async extraction

    updated_slots = user.claims.list()
    print("\nUpdated slots:", updated_slots)

    print("\n✅ Claims example complete!")


if __name__ == "__main__":
    main()
