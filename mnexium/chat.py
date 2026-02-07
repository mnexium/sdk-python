"""
Chat - A conversation thread with a stable chat_id
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Union

from .types import (
    ChatOptions,
    ChatProcessOptions,
    ProcessOptions,
    ProcessResponse,
)

if TYPE_CHECKING:
    from .client import Mnexium
    from .streaming import StreamResponse


class Chat:
    """
    Chat represents a conversation thread with a stable chat_id.

    Chats belong to a Subject and maintain conversation history.

    Example::

        chat = alice.create_chat(ChatOptions(history=True))
        response = chat.process("Hello!")
        response2 = chat.process("What did I just say?")
    """

    def __init__(
        self,
        client: Mnexium,
        subject_id: str,
        options: Optional[ChatOptions] = None,
    ) -> None:
        opts = options or ChatOptions()
        self._client = client
        self.subject_id = subject_id
        self.id = opts.chat_id or str(uuid.uuid4())
        self._options = opts

    def process(
        self, input: Union[str, ChatProcessOptions]
    ) -> Union[ProcessResponse, StreamResponse]:
        """
        Process a message in this chat.

        Args:
            input: A string message or ChatProcessOptions for full control.

        Returns:
            ProcessResponse for non-streaming, StreamResponse for streaming.

        Example::

            # Non-streaming
            response = chat.process("Hello!")

            # Streaming
            stream = chat.process(ChatProcessOptions(content="Hello!", stream=True))
            for chunk in stream:
                print(chunk.content, end="", flush=True)
        """
        if isinstance(input, str):
            opts = ChatProcessOptions(content=input)
        else:
            opts = input

        def _pick(per_msg: Optional[object], chat_default: Optional[object]) -> Optional[object]:
            return per_msg if per_msg is not None else chat_default

        return self._client.process(ProcessOptions(
            content=opts.content,
            chat_id=self.id,
            subject_id=self.subject_id,
            model=_pick(opts.model, self._options.model),
            log=_pick(opts.log, self._options.log),
            learn=_pick(opts.learn, self._options.learn),
            recall=_pick(opts.recall, self._options.recall),
            profile=_pick(opts.profile, self._options.profile),
            history=_pick(opts.history, self._options.history),
            summarize=_pick(opts.summarize, self._options.summarize),
            system_prompt=_pick(opts.system_prompt, self._options.system_prompt),
            max_tokens=_pick(opts.max_tokens, self._options.max_tokens),
            temperature=_pick(opts.temperature, self._options.temperature),
            stream=opts.stream,
            metadata=_pick(opts.metadata, self._options.metadata),
            regenerate_key=opts.regenerate_key,
        ))
