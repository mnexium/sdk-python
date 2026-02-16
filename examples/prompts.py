"""
Mnexium SDK - System Prompts Example

Demonstrates system prompt management:
- Create prompts
- List prompts
- Update prompts
- Resolve prompts
- Delete prompts

Run with: python prompts.py
"""

import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

from mnexium import Mnexium, ProviderConfig, SystemPromptCreateOptions, ChatOptions


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

    print("📝 Mnexium System Prompts Example\n")

    # --- Create a prompt ---
    print("--- Creating prompts ---\n")

    prompt = mnx.prompts.create(SystemPromptCreateOptions(
        name="Customer Support",
        prompt_text="You are a helpful customer support agent. Be friendly and concise.",
        is_default=True,
    ))
    prompt_id = prompt.get("id", prompt) if isinstance(prompt, dict) else prompt
    print("Created prompt:", prompt_id)

    prompt2 = mnx.prompts.create(SystemPromptCreateOptions(
        name="Technical Assistant",
        prompt_text="You are a technical assistant. Provide detailed, accurate answers.",
    ))
    prompt2_id = prompt2.get("id", prompt2) if isinstance(prompt2, dict) else prompt2
    print("Created prompt:", prompt2_id)

    # --- List prompts ---
    print("\n--- Listing prompts ---\n")

    prompts = mnx.prompts.list()
    print(f"Total prompts: {len(prompts)}")
    for p in prompts:
        name = p.get("name", "?") if isinstance(p, dict) else "?"
        pid = p.get("id", "?") if isinstance(p, dict) else "?"
        print(f"  - [{pid}] {name}")

    # --- Update a prompt ---
    if isinstance(prompt, dict) and "id" in prompt:
        print("\n--- Updating prompt ---\n")

        mnx.prompts.update(
            prompt["id"],
            prompt_text="You are a helpful and empathetic customer support agent. Always greet the user warmly.",
        )
        print("Updated prompt:", prompt["id"])

    # --- Resolve prompts ---
    print("\n--- Resolving prompts ---\n")

    resolved = mnx.prompts.resolve(subject_id="prompts-demo-user")
    print("Resolved:", resolved)

    # --- Use prompt in chat ---
    if isinstance(prompt, dict) and "id" in prompt:
        print("\n--- Using prompt in chat ---\n")

        user = mnx.subject("prompts-demo-user")
        chat = user.create_chat(ChatOptions(
            model="gpt-4o-mini",
            system_prompt=prompt["id"],
        ))
        response = chat.process("Hi, I need help with my account.")
        print("AI:", (response.content or "")[:150])

    # --- Delete prompts ---
    print("\n--- Cleaning up ---\n")

    if isinstance(prompt, dict) and "id" in prompt:
        mnx.prompts.delete(prompt["id"])
        print("Deleted:", prompt["id"])
    if isinstance(prompt2, dict) and "id" in prompt2:
        mnx.prompts.delete(prompt2["id"])
        print("Deleted:", prompt2["id"])

    print("\n✅ Prompts example complete!")


if __name__ == "__main__":
    main()
