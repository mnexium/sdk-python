"""
Mnexium SDK - Memories Example

Demonstrates memory management:
- Add memories
- Search memories (semantic)
- List memories
- Update and delete memories
- Superseded memories

Run with: python memories.py
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

    print("🧠 Mnexium Memories Example\n")

    user = mnx.subject("memories-demo")

    # --- Add memories ---
    print("--- Adding memories ---\n")

    mem1 = user.memories.add("I love hiking in the mountains", source="user_input")
    print("Added:", mem1.get("id", mem1) if isinstance(mem1, dict) else mem1)

    mem2 = user.memories.add("My favorite programming language is Python")
    print("Added:", mem2.get("id", mem2) if isinstance(mem2, dict) else mem2)

    mem3 = user.memories.add("I work remotely from Denver, Colorado")
    print("Added:", mem3.get("id", mem3) if isinstance(mem3, dict) else mem3)

    # --- Search memories ---
    print("\n--- Searching memories ---\n")

    results = user.memories.search("outdoor activities", limit=3)
    print(f"Search 'outdoor activities' ({len(results)} results):")
    for r in results:
        text = r.get("text", str(r))[:60] if isinstance(r, dict) else str(r)[:60]
        print(f"  - {text}")

    results2 = user.memories.search("programming", limit=3)
    print(f"\nSearch 'programming' ({len(results2)} results):")
    for r in results2:
        text = r.get("text", str(r))[:60] if isinstance(r, dict) else str(r)[:60]
        print(f"  - {text}")

    # --- List all memories ---
    print("\n--- Listing all memories ---\n")

    all_mems = user.memories.list(limit=10)
    print(f"Total: {len(all_mems)} memories")
    for m in all_mems:
        text = m.get("text", str(m))[:50] if isinstance(m, dict) else str(m)[:50]
        mid = m.get("id", "?") if isinstance(m, dict) else "?"
        print(f"  [{mid}] {text}")

    # --- Get a specific memory ---
    if isinstance(mem1, dict) and "id" in mem1:
        print("\n--- Get specific memory ---\n")
        fetched = user.memories.get(mem1["id"])
        print("Fetched:", fetched)

    # --- Delete a memory ---
    if isinstance(mem3, dict) and "id" in mem3:
        print("\n--- Deleting a memory ---\n")
        user.memories.delete(mem3["id"])
        print(f"Deleted memory {mem3['id']}")

        remaining = user.memories.list(limit=10)
        print(f"Remaining: {len(remaining)} memories")

    # --- Superseded memories ---
    print("\n--- Superseded memories ---\n")
    superseded = user.memories.superseded()
    print(f"Superseded: {len(superseded)} memories")

    print("\n✅ Memories example complete!")


if __name__ == "__main__":
    main()
