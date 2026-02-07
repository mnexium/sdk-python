# mnexium

Official Mnexium SDK for Python. Add persistent memory, conversation history, user profiles, and agent state to your AI apps.

Works with **OpenAI**, **Anthropic**, and **Google Gemini**. Bring your own API key.

## Installation

```bash
pip install mnexium
```

## Quick Start

```python
import os
from mnexium import Mnexium, ProviderConfig

mnx = Mnexium(
    api_key="mnx_...",  # Optional - auto-provisions trial key if omitted
    openai=ProviderConfig(api_key=os.environ["OPENAI_API_KEY"]),
)

# Get a Subject handle (no network call)
alice = mnx.subject("user_123")
# Or auto-generate an ID:
anon = mnx.subject()

# Simple one-off message
response = alice.process("Hello!")
print(response.content)

# Multi-turn chat with history
from mnexium import ChatOptions

chat = alice.create_chat(ChatOptions(history=True, learn=True, recall=True))
chat.process("My favorite color is blue")
chat.process("What is my favorite color?")  # Remembers!
```

## Core Concepts

### Subject

A **Subject** is a logical identity (user, agent, org, device) that owns memory, profile, and state. Creating a Subject is instant — no network call.

```python
alice = mnx.subject("user_123")

# Subject owns all resources
alice.memories.search("hobbies")
alice.memories.list()
alice.profile.get()
alice.state.get("preferences")
alice.claims.get("favorite_color")
alice.chats.list()
```

### Chat

A **Chat** is a conversation thread with a stable `chat_id`. Chats belong to a Subject.

```python
from mnexium import ChatOptions

chat = alice.create_chat(ChatOptions(
    model="gpt-4o-mini",
    history=True,    # Include previous messages
    learn=True,      # Extract memories from conversation
    recall=True,     # Inject relevant memories into context
    profile=True,    # Include user profile in context
))

chat.process("Hello!")
chat.process("What did I just say?")  # Has history
```

### Streaming

Real-time streaming responses:

```python
from mnexium import ChatProcessOptions

stream = chat.process(ChatProcessOptions(content="Tell me a story", stream=True))

for chunk in stream:
    print(chunk.content, end="", flush=True)

# Metadata available after stream completes
print(stream.total_content)  # Full accumulated text
print(stream.usage)          # Token counts
print(stream.chat_id)        # Chat ID

# Or collect the full response at once
stream2 = chat.process(ChatProcessOptions(content="Summarize", stream=True))
text = stream2.text()
```

### Multi-Provider Support

The SDK auto-detects the provider from the model name:

```python
mnx = Mnexium(
    openai=ProviderConfig(api_key=os.environ["OPENAI_API_KEY"]),
    anthropic=ProviderConfig(api_key=os.environ["ANTHROPIC_API_KEY"]),
    google=ProviderConfig(api_key=os.environ["GOOGLE_API_KEY"]),
)

alice = mnx.subject("user_123")
chat = alice.create_chat(ChatOptions(learn=True, recall=True))

# Switch models freely — memories are shared across providers
chat.process(ChatProcessOptions(content="I love hiking", model="gpt-4o-mini"))
chat.process(ChatProcessOptions(content="What do I love?", model="claude-sonnet-4-20250514"))
chat.process(ChatProcessOptions(content="Tell me my hobbies", model="gemini-2.0-flash"))
```

## API Reference

### Memories

```python
# Add a memory
mem = alice.memories.add("User prefers dark mode", source="settings")

# List memories
memories = alice.memories.list(limit=50)

# Semantic search
results = alice.memories.search("preferences", limit=5)

# Get a specific memory
memory = alice.memories.get("mem_abc123")

# Update a memory
alice.memories.update("mem_abc123", text="Updated text")

# Delete a memory
alice.memories.delete("mem_abc123")

# List superseded memories
old = alice.memories.superseded()

# Restore a superseded memory
alice.memories.restore("mem_abc123")

# Query recall events (which memories were used in a chat)
recalls = alice.memories.recalls(chat_id="chat_xyz")
```

### Real-time Memory Events

Subscribe to memory changes via SSE:

```python
events = alice.memories.subscribe()

for event in events:
    if event.type == "memory.created":
        print("New memory:", event.data)
    elif event.type == "memory.superseded":
        print("Memory replaced:", event.data)
    elif event.type == "memory.deleted":
        print("Memory removed:", event.data)

# Close the connection
events.close()
```

Event types: `connected`, `memory.created`, `memory.updated`, `memory.deleted`, `memory.superseded`, `profile.updated`, `heartbeat`

### Claims (Structured Facts)

```python
# Set a claim
alice.claims.set("favorite_color", "blue", confidence=0.95)

# Get a specific slot
color = alice.claims.get("favorite_color")

# List all claim slots
slots = alice.claims.list()

# Get current truth (all active values)
truth = alice.claims.truth()

# Get claim history
history = alice.claims.history()

# Retract a claim
alice.claims.retract("clm_abc123")
```

### Profile

```python
# Get profile
profile = alice.profile.get()

# Update profile fields
alice.profile.update([
    {"field_key": "display_name", "value": "Alice"},
    {"field_key": "timezone", "value": "America/New_York"},
])

# Delete a profile field
alice.profile.delete_field("timezone")
```

### Agent State

Persist key-value state for workflows, wizards, and agent continuity:

```python
# Set state (with optional TTL)
alice.state.set("current_task", {"step": 3}, ttl_seconds=3600)

# Get state
task = alice.state.get("current_task")

# Delete state
alice.state.delete("current_task")
```

### Chat History

```python
# List recent chats
from mnexium import ChatHistoryListOptions

chats = alice.chats.list(ChatHistoryListOptions(limit=10))

# Read messages from a specific chat
messages = alice.chats.read("chat_abc123")

# Delete a chat
alice.chats.delete("chat_abc123")
```

### System Prompts

```python
from mnexium import SystemPromptCreateOptions

# Create a prompt
prompt = mnx.prompts.create(SystemPromptCreateOptions(
    name="Customer Support",
    prompt_text="You are a helpful customer support agent...",
    is_default=True,
))

# List all prompts
prompts = mnx.prompts.list()

# Update a prompt
mnx.prompts.update(prompt["id"], prompt_text="Updated instructions...")

# Preview which prompts will be injected
resolved = mnx.prompts.resolve(subject_id="user_123")

# Use in chat
chat = alice.create_chat(ChatOptions(system_prompt=prompt["id"]))

# Delete a prompt
mnx.prompts.delete(prompt["id"])
```

## Configuration

```python
from mnexium import Mnexium, ProviderConfig, MnexiumDefaults

mnx = Mnexium(
    api_key="mnx_...",                    # Optional — auto-provisions trial key
    base_url="https://mnexium.com/api/v1",  # API base URL
    timeout=30.0,                         # Request timeout (seconds)
    max_retries=2,                        # Retry count for failed requests
    openai=ProviderConfig(api_key="..."),    # OpenAI config
    anthropic=ProviderConfig(api_key="..."), # Anthropic config
    google=ProviderConfig(api_key="..."),    # Google config
    defaults=MnexiumDefaults(             # Default options for all process() calls
        model="gpt-4o-mini",
        learn=True,
        recall=False,
        profile=False,
        history=True,
    ),
)
```

### Mnx Parameters

Every `process()` and `chat.process()` call supports these options:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | `"gpt-4o-mini"` | Model to use |
| `learn` | bool/`"force"` | `True` | Extract memories from conversation |
| `recall` | bool | `False` | Inject relevant memories into context |
| `profile` | bool | `False` | Include user profile in context |
| `history` | bool | `True` | Prepend previous messages from this chat |
| `log` | bool | `True` | Save messages to chat history |
| `summarize` | bool/str | `False` | `"light"`, `"balanced"`, or `"aggressive"` |
| `system_prompt` | bool/str | `True` | `True` (auto), `False` (skip), or prompt ID |
| `stream` | bool | `False` | Enable streaming response |
| `metadata` | dict | — | Custom metadata attached to saved logs |

## Trial Keys

If you don't provide an API key, Mnexium auto-provisions a trial key:

```python
mnx = Mnexium(
    openai=ProviderConfig(api_key=os.environ["OPENAI_API_KEY"]),
)

alice = mnx.subject("user_123")
alice.process("Hello!")

# Get the provisioned key to save it
trial = mnx.get_trial_info()
if trial:
    print("Save this key:", trial["key"])
```

Claim your trial key at [mnexium.com/claim](https://mnexium.com/claim).

## Error Handling

```python
from mnexium import Mnexium, AuthenticationError, RateLimitError, APIError

try:
    alice.process("Hello!")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Current: {e.current}, Limit: {e.limit}")
except APIError as e:
    print(f"API error {e.status}: {e}")
```

## Raw Response

Access the full API response for advanced use:

```python
response = chat.process("Hello!")
print(response.raw)       # Full API response dict
print(response.chat_id)   # Chat ID
print(response.usage)     # UsageInfo(prompt_tokens, completion_tokens, total_tokens)
```

## Examples

See the [examples/](./examples/) directory for runnable demos:

| Example | Description |
|---------|-------------|
| `hello_world.py` | Hello world — chat, history, recall |
| `streaming.py` | Real-time streaming responses |
| `events.py` | Real-time memory event subscriptions |
| `memories.py` | Add, list, search, delete memories |
| `claims.py` | Claims extraction and manual setting |
| `state.py` | Agent state with TTL |
| `profile.py` | User profiles |
| `prompts.py` | System prompt management |
| `multi_provider.py` | Multi-provider (OpenAI, Claude, Gemini) |
| `full_demo.py` | Full API demo |

## Supported Models

- **OpenAI:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo, o1, o1-mini, o3
- **Anthropic:** claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-3-5-sonnet, claude-sonnet-4
- **Google Gemini:** gemini-2.0-flash-lite, gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash

## Links

- [Documentation](https://mnexium.com/docs)
- [Blog](https://mnexium.com/blogs)
- [Sign Up](https://mnexium.com)

## License

MIT
