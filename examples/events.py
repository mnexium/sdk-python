"""
Mnexium SDK - Real-time Events Example

Demonstrates subscribing to real-time memory events via SSE:
1. Subscribe to memory events for a subject
2. Add memories and watch events arrive in real-time
3. Gracefully close the event stream

Run with: python events.py
"""

import os
import sys
import time
import threading

from dotenv import load_dotenv

load_dotenv()

from mnexium import Mnexium, ProviderConfig, ChatOptions


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

    print("📡 Mnexium Real-time Events Example\n")

    user = mnx.subject(f"events-demo-{int(time.time())}")
    print("Subject ID:", user.id)

    # Subscribe to memory events
    print("\n--- Subscribing to memory events ---\n")
    events = user.memories.subscribe()

    # Process events in a background thread
    event_count = 0

    def listen():
        nonlocal event_count
        for event in events:
            event_count += 1
            if event.type == "connected":
                print("✅ Connected to event stream")
                print("   Project:", event.data.get("project_id"))
            elif event.type == "heartbeat":
                print("💓 Heartbeat:", event.data.get("timestamp"))
            else:
                import json
                print(f"📨 Event #{event_count}: {event.type}")
                print("   Data:", json.dumps(event.data, indent=2)[:200])

            # Stop after receiving a few events (for demo purposes)
            if event_count >= 6:
                print("\n--- Closing event stream after 6 events ---")
                events.close()
                break

    listener = threading.Thread(target=listen, daemon=True)
    listener.start()

    # Wait a moment for connection to establish
    time.sleep(1)

    # Now trigger some memory events by adding memories
    print("\n--- Adding memories (will trigger events) ---\n")

    mem1 = user.memories.add("I enjoy playing chess on weekends")
    print("Added memory:", mem1.get("id", mem1) if isinstance(mem1, dict) else mem1)

    time.sleep(0.5)

    mem2 = user.memories.add("My favorite cuisine is Japanese")
    print("Added memory:", mem2.get("id", mem2) if isinstance(mem2, dict) else mem2)

    time.sleep(0.5)

    # Chat with learn=True to trigger memory extraction
    chat = user.create_chat(ChatOptions(model="gpt-4o-mini", learn=True))
    chat.process("I work as a data scientist at a biotech company.")
    print("Sent chat message (learn=True)")

    # Wait for events to arrive
    print("\nWaiting for events...\n")
    listener.join(timeout=10)

    # Clean up
    events.close()

    print(f"\nReceived {event_count} events total")
    print("\n✅ Events example complete!")
    print("\nKey takeaways:")
    print("  - user.memories.subscribe() opens an SSE connection")
    print("  - Events arrive in real-time as memories are created/updated")
    print("  - Call events.close() to disconnect")


if __name__ == "__main__":
    main()
