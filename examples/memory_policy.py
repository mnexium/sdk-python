"""
Mnexium SDK - Memory Policy Override Example

Demonstrates per-request memory policy control:
- memory_policy="policy_id" to force a specific policy
- memory_policy=False to disable memory policy for that request
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from mnexium import (
    ChatCompletionOptions,
    ChatMessage,
    ChatOptions,
    ChatProcessOptions,
    Mnexium,
    ProviderConfig,
)

load_dotenv()


def main() -> None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("⏭️  Skipping: OPENAI_API_KEY not set")
        return

    mnx = Mnexium(
        api_key=os.environ.get("MNX_KEY"),
        base_url=os.environ.get("MNX_BASE_URL"),
        openai=ProviderConfig(api_key=openai_key),
    )

    user = mnx.subject("memory-policy-demo")
    chat = user.create_chat(ChatOptions(history=True, learn=True, recall=True))

    print("1) Force memory policy by ID")
    r1 = chat.process(ChatProcessOptions(
        content="Remember that I prefer aisle seats.",
        memory_policy="mpol_default",
    ))
    print((r1.content or "")[:120])

    print("\n2) Disable memory policy for one request")
    r2 = chat.process(ChatProcessOptions(
        content="This message should not use memory policy.",
        memory_policy=False,
    ))
    print((r2.content or "")[:120])

    print("\n3) Low-level chat.completions with memory_policy")
    r3 = mnx.chat.completions.create(ChatCompletionOptions(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Say hello briefly.")],
        memory_policy="mpol_default",
    ))
    print(r3.choices[0].message.content[:120])


if __name__ == "__main__":
    main()
