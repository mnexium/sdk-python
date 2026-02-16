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

        return self._client.process(ProcessOptions(
            content=opts.content,
            chat_id=self.id,
            subject_id=self.subject_id,
            model=opts.model if opts.model is not None else self._options.model,
            log=opts.log if opts.log is not None else self._options.log,
            learn=opts.learn if opts.learn is not None else self._options.learn,
            recall=opts.recall if opts.recall is not None else self._options.recall,
            profile=opts.profile if opts.profile is not None else self._options.profile,
            history=opts.history if opts.history is not None else self._options.history,
            summarize=opts.summarize if opts.summarize is not None else self._options.summarize,
            system_prompt=(
                opts.system_prompt
                if opts.system_prompt is not None
                else self._options.system_prompt
            ),
            max_tokens=opts.max_tokens if opts.max_tokens is not None else self._options.max_tokens,
            temperature=(
                opts.temperature
                if opts.temperature is not None
                else self._options.temperature
            ),
            stream=opts.stream,
            metadata=opts.metadata if opts.metadata is not None else self._options.metadata,
            regenerate_key=opts.regenerate_key,
            records=opts.records,
        ))
