"""
Mnexium SDK - Agent State Example

Demonstrates key-value state persistence:
- Set state with optional TTL
- Get state
- Delete state

Run with: python state.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from mnexium import Mnexium, ProviderConfig


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

    print("💾 Mnexium Agent State Example\n")

    user = mnx.subject("state-demo")

    # --- Set state ---
    print("--- Setting state ---\n")

    user.state.set("current_task", {"step": 3, "total_steps": 5})
    print("Set: current_task")

    user.state.set("preferences", {"theme": "dark", "language": "en"})
    print("Set: preferences")

    user.state.set("temp_cache", "this-will-expire", ttl_seconds=60)
    print("Set: temp_cache (TTL: 60s)")

    # --- Get state ---
    print("\n--- Getting state ---\n")

    task = user.state.get("current_task")
    print("current_task:", task)

    prefs = user.state.get("preferences")
    print("preferences:", prefs)

    cache = user.state.get("temp_cache")
    print("temp_cache:", cache)

    # --- Get non-existent key ---
    print("\n--- Non-existent key ---\n")

    missing = user.state.get("does_not_exist")
    print("does_not_exist:", missing)  # Should be None

    # --- Delete state ---
    print("\n--- Deleting state ---\n")

    user.state.delete("temp_cache")
    print("Deleted: temp_cache")

    after_delete = user.state.get("temp_cache")
    print("temp_cache after delete:", after_delete)  # Should be None

    # --- Cleanup ---
    user.state.delete("current_task")
    user.state.delete("preferences")
    print("\nCleaned up remaining state")

    print("\n✅ State example complete!")


if __name__ == "__main__":
    main()
