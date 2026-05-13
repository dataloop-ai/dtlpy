from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union

from .. import entities
from .llm_context import LLMContext

logger = logging.getLogger(name='dtlpy')


class LLMMessage(entities.DlEntity):
    """
    Represents a single message in an LLM conversation trace.

    Uses a single internal ``_dict`` dict as the source of truth.
    Known fields (``role``, ``content``) are exposed via DlProperty descriptors;
    any additional fields live directly in ``_dict``.

    :param str role: Message role (``"user"``, ``"assistant"``, ``"system"``, ``"tool"``, etc.)
    :param content: Optional message content (str, list, dict, or None)
    :param kwargs: Arbitrary extra fields stored in the message body
    """

    role: str = entities.DlProperty(location=['role'], _type=str)
    content = entities.DlProperty(location=['content'])
    context: entities.DlList = entities.DlProperty(location=['context'], _kls='LLMContext')

    @staticmethod
    def _validate_dict(json_data: dict):
        """Raise if *json_data* is not a dict or lacks a ``role``."""
        if not isinstance(json_data, dict):
            raise ValueError(f"Expected dict, got {type(json_data)}")
        if 'role' not in json_data:
            raise ValueError("'role' is required in message JSON")

    def __init__(self, data_dict=None, **kwargs):
        data_dict = self._split_kwargs(data_dict=data_dict, kwargs=kwargs)
        super().__init__(_dict=data_dict, **kwargs)
        self._validate_dict(json_data=self._dict)

    def to_json(self) -> dict:
        """
        Return the message as a plain dict.

        Returns ``_dict`` by reference (not a copy) so that mutations
        propagate back to the parent trace's messages list.

        :return: message dict
        :rtype: dict
        """
        return self._dict

    @classmethod
    def from_json(cls, json_data: dict) -> LLMMessage:
        """
        Create an LLMMessage from a dict.

        :param dict json_data: message dict (must contain ``role``)
        :return: LLMMessage instance
        :rtype: LLMMessage
        """
        cls._validate_dict(json_data=json_data)
        return cls(data_dict=json_data)

    def add_context(self, contexts: List[Union[entities.LLMContext, dict]]):
        """
        Append retrieval context entries to this message.

        :param list contexts: list of :class:`LLMContext` instances or raw dicts
            (each dict must include at least one of ``text`` or ``item_id``)

        **Example**:

        .. code-block:: python

            msg.add_context([
                dl.LLMContext(text="Deep Research is a new capability...",
                              item_id="64a7f...", score=0.98),
            ])
        """
        if self.context is None:
            self.context = []
        # Cache the DlList locally; each `self.context` access reconstructs a new wrapper.
        ctx_list = self.context
        for ctx in contexts:
            if isinstance(ctx, dict):
                ctx = LLMContext.from_json(json_data=ctx)
            if not isinstance(ctx, LLMContext):
                raise ValueError(f"Expected LLMContext or dict, got {type(ctx)}")
            ctx_list.append(ctx)

    def get_context(self) -> list:
        """
        Get retrieval context entries attached to this message.

        :return: list of :class:`LLMContext` instances, or empty list
        :rtype: list[LLMContext]

        **Example**:

        .. code-block:: python

            for ctx in msg.get_context():
                print(ctx.text, ctx.score)
        """
        return list(self.context) if self.context is not None else []

    def build_context(self, metadata_fields: list = None) -> str:
        """
        Render context entries into a text block suitable for injection
        into an LLM prompt.

        Produces the same ``<source>/<text>`` format used by
        :meth:`PromptItem.build_context` for backward compatibility with
        existing model adapters.

        If a context entry has no ``text`` but has an ``item_id``, the text
        is fetched from the platform.

        :param list metadata_fields: metadata key paths to include in ``<source>``
            tags, e.g. ``['system.document.source']``
        :return: rendered context string, empty string if no context
        :rtype: str

        **Example**:

        .. code-block:: python

            context = msg.build_context()
            if context:
                prompt.append({"role": "assistant", "content": context})
        """
        if metadata_fields is None:
            metadata_fields = []

        ctx_list = self.context
        if not ctx_list:
            return ""

        with ThreadPoolExecutor(max_workers=32) as pool:
            results = pool.map(
                lambda ctx: ctx.resolve_text(metadata_fields=metadata_fields),
                ctx_list,
            )
            context = ""
            for text, source_parts in results:
                context += f"\n<source>\n{source_parts}\n</source>\n<text>\n{text}\n</text>"
            return context

    def __repr__(self):
        return f'<LLMMessage role={self.role!r}>'
