"""
Mnexium SDK - Full API Demo

A comprehensive example showcasing ALL SDK capabilities:
- Subject-centric API
- Chat with history, learn, recall
- Memories (add, search, list, delete)
- Claims (structured facts)
- State (key-value persistence)
- Profile (aggregated view)
- Chat History listing
- Simple process (ephemeral)

Run with: python full_demo.py
"""

import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

from mnexium import (
    Mnexium,
    ProviderConfig,
    MnexiumDefaults,
    ChatOptions,
)


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("⏭️  Skipping: OPENAI_API_KEY not set")
        return

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
        defaults=MnexiumDefaults(
            model="gpt-4o-mini",
            learn=True,
            recall=True,
            history=True,
        ),
    )

    print("🚀 Mnexium Full API Demo\n")
    print("=" * 50)

    # ============================================================
    # 1. SUBJECT
    # ============================================================
    print("\n📌 1. SUBJECT\n")

    user = mnx.subject("full-demo-user")
    print("Created subject handle:", user.id)
    print("(No network call - just a scoped handle)")

    # ============================================================
    # 2. MEMORIES
    # ============================================================
    print("\n📌 2. MEMORIES\n")

    mem1 = user.memories.add(
        "I am a software developer specializing in Python",
        source="user_input",
    )
    print("Added memory:", mem1.get("id", mem1))

    user.memories.add("My favorite framework is FastAPI")
    user.memories.add("I prefer dark mode in all my applications")
    print("Added 2 more memories")

    search_results = user.memories.search("programming preferences", limit=3)
    print(f"\nSearch results ({len(search_results)}):")
    for r in search_results:
        text = r.get("text", str(r))[:40] if isinstance(r, dict) else str(r)[:40]
        print(f"  - {text}...")

    all_mems = user.memories.list(limit=5)
    print(f"\nTotal memories: {len(all_mems)}")

    # ============================================================
    # 3. CLAIMS
    # ============================================================
    print("\n📌 3. CLAIMS\n")

    user.claims.set("name", "Demo User", confidence=1.0)
    user.claims.set("role", "developer", confidence=0.95)
    user.claims.set("experience_years", 5, confidence=0.8)
    print("Set 3 claims")

    name = user.claims.get("name")
    print("Retrieved claim - name:", name.get("value") if isinstance(name, dict) else name)

    all_claims = user.claims.list()
    print("All claims:", len(all_claims) if isinstance(all_claims, dict) else all_claims, "slots")

    # ============================================================
    # 4. STATE
    # ============================================================
    print("\n📌 4. STATE\n")

    user.state.set("current_project", "mnexium-demo")
    user.state.set("session_data", {
        "start_time": "2024-01-15T10:00:00Z",
        "actions": ["login", "view_dashboard"],
    })
    user.state.set("temp_cache", "expires-soon", ttl_seconds=300)
    print("Set 3 state keys (1 with TTL)")

    project = user.state.get("current_project")
    print("Retrieved state - current_project:", project.get("value") if isinstance(project, dict) else project)

    # ============================================================
    # 5. CHAT WITH HISTORY & LEARNING
    # ============================================================
    print("\n📌 5. CHAT WITH HISTORY & LEARNING\n")

    chat = user.create_chat(ChatOptions(
        model="gpt-4o-mini",
        learn=True,
        history=True,
        recall=True,
    ))
    print("Created chat:", chat.id)

    r1 = chat.process("Hi! My favorite color is purple.")
    print("\nUser: Hi! My favorite color is purple.")
    print("AI:", (r1.content or "")[:100] + "...")

    r2 = chat.process("What color did I just mention?")
    print("\nUser: What color did I just mention?")
    print("AI:", (r2.content or "")[:100] + "...")

    # ============================================================
    # 6. MEMORY RECALL ACROSS CHATS
    # ============================================================
    print("\n📌 6. MEMORY RECALL ACROSS CHATS\n")

    chat2 = user.create_chat(ChatOptions(
        model="gpt-4o-mini",
        recall=True,
    ))
    print("Created new chat:", chat2.id)

    r3 = chat2.process("What do you know about my programming preferences?")
    print("User: What do you know about my programming preferences?")
    print("AI:", (r3.content or "")[:150] + "...")

    # ============================================================
    # 7. CHAT HISTORY
    # ============================================================
    print("\n📌 7. CHAT HISTORY\n")

    chat_history = user.chats.list()
    print(f"Recent chats ({len(chat_history)}):")
    for c in chat_history:
        print(f"  - {c.chat_id} ({c.message_count or '?'} messages)")

    # ============================================================
    # 8. PROFILE
    # ============================================================
    print("\n📌 8. PROFILE\n")

    profile = user.profile.get()
    print("Profile summary:")
    if isinstance(profile, dict):
        print("  Subject ID:", profile.get("subject_id"))
        print("  Memory count:", profile.get("memory_count", "N/A"))
        print("  Claims:", len(profile.get("claims", {})) if isinstance(profile.get("claims"), dict) else "N/A")

    # ============================================================
    # 9. SIMPLE PROCESS (No Chat)
    # ============================================================
    print("\n📌 9. SIMPLE PROCESS (Ephemeral)\n")

    simple = user.process("What is 2 + 2?")
    print("Quick question: What is 2 + 2?")
    print("Answer:", simple.content)

    # ============================================================
    # 10. TRIAL KEY INFO
    # ============================================================
    print("\n📌 10. TRIAL KEY INFO\n")

    trial = mnx.get_trial_info()
    if trial:
        print("Trial key provisioned:", trial["key"][:20] + "...")
        print("Claim URL:", trial["claim_url"])
    else:
        print("Using existing API key (no trial provisioned)")

    # ============================================================
    # CLEANUP
    # ============================================================
    print("\n📌 CLEANUP\n")

    user.state.delete("temp_cache")
    print("Deleted temp state")

    print("\n" + "=" * 50)
    print("✅ Full API demo complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
