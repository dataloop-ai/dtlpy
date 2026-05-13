from __future__ import annotations

import logging
import json
import io
import os
from typing import List, Union, Optional

from dtlpy.services.api_client import client as client_api
from .. import entities, repositories
from .llm_message import LLMMessage
from .llm_context import LLMContext

logger = logging.getLogger(name='dtlpy')


class LLMTrace(entities.DlEntity):
    """
    Represents a trace of an LLM conversation session.

    Uses a single internal ``_dict`` dict as the source of truth.
    The enforced fields are ``shebang`` (always ``"dataloop"``),
    ``metadata`` (always contains ``{"dltype": "llm_trace"}``), and
    ``messages`` (a list).  Everything else is free-form and stored
    directly in ``_dict``.

    The trace is persisted as a regular JSON file item in a Dataloop dataset.

    :param str name: Filename for the trace (e.g. ``"session_001.json"``)
    :param item: Optional Dataloop Item (when loaded from platform)
    :param kwargs: Arbitrary extra fields stored in the trace body

    **Example**:

    .. code-block:: python

        trace = dl.LLMTrace(name="session.json")
        trace.add_message(dl.LLMMessage(role="user", content="Hello"))
        trace.add_message(dl.LLMMessage(role="assistant", content="Hi!"))
        trace._dict["model"] = "gpt-4o"
        dataset.items.upload(local_path=trace)
    """

    shebang: str = entities.DlProperty(location=['shebang'], _type=str, default='dataloop')
    messages: list = entities.DlProperty(location=['messages'], default=lambda self: [], _kls='LLMMessage')
    metadata: dict = entities.DlProperty(location=['metadata'], _type=dict, default=lambda self: {'dltype': 'llm_trace'})

    @staticmethod
    def _validate_dict(json_data: dict):
        """Raise if *json_data* is not a dict or lacks a ``messages`` list."""
        if not isinstance(json_data, dict):
            raise ValueError(f"Expected dict, got {type(json_data)}")
        if 'messages' not in json_data or not isinstance(json_data['messages'], list):
            raise ValueError("'messages' list is required in trace JSON")

    def __init__(self, name: str, data_dict=None, item: entities.Item = None, **kwargs):
        # free-form kwargs are moved to data_dict and DlProperty keys and is_fetched are kept for DlEntity.__init__
        data_dict = self._split_kwargs(data_dict=data_dict, kwargs=kwargs)
        data_dict.setdefault('metadata', {}).setdefault('dltype', 'llm_trace')
        super().__init__(_dict=data_dict, **kwargs)

        self.name = name
        self._item = item

        if item is not None:
            self.fetch()

    @property
    def item(self) -> Optional[entities.Item]:
        """
        Get the underlying Item object.

        :return: Item or None
        :rtype: Optional[dtlpy.entities.Item]
        """
        return self._item

    @item.setter
    def item(self, item: Optional[entities.Item]):
        if item is not None and not isinstance(item, entities.Item):
            raise ValueError(f"Expected dtlpy.entities.Item or None, got {type(item)}")
        self._item = item

    def add_message(self, message: Union[LLMMessage, dict]):
        """
        Append a message to the trace.

        :param message: an LLMMessage instance or a raw dict (must contain ``role``)

        **Example**:

        .. code-block:: python

            trace.add_message(dl.LLMMessage(role="user", content="Hello"))
            trace.add_message({"role": "assistant", "content": "Hi!"})
        """
        if isinstance(message, dict):
            message = LLMMessage.from_json(json_data=message)
        if not isinstance(message, LLMMessage):
            raise ValueError(f"Expected LLMMessage or dict, got {type(message)}")
        self.messages.append(message)

    def _get_message(self, message_index: int) -> LLMMessage:
        """Return the LLMMessage at *message_index*, with bounds checking."""
        try:
            return self.messages[message_index]
        except IndexError:
            raise IndexError(f"message_index {message_index} is out of range (trace has {len(self.messages)} messages)")

    def add_context(self, contexts: List[Union[LLMContext, dict]], message_index: int = -1):
        """
        Attach retrieval context entries to a specific message in the trace.

        This is the **retriever access point**. Each context entry represents a
        document or chunk retrieved by a RAG pipeline. Delegates to
        :meth:`LLMMessage.add_context`.

        :param list contexts: list of :class:`LLMContext` instances or raw dicts
            (each dict must include at least one of ``text`` or ``item_id``)
        :param int message_index: index of the target message in
            :attr:`messages` (default ``-1``, the last message)

        **Example**:

        .. code-block:: python

            trace.add_context([
                dl.LLMContext(text="Deep Research is a new capability...",
                              item_id="64a7f...", score=0.98),
                dl.LLMContext(text="External knowledge base result...",
                              score=0.85),
            ])
        """
        self._get_message(message_index=message_index).add_context(contexts=contexts)

    def get_context(self, message_index: int = -1) -> List[LLMContext]:
        """
        Get retrieval context entries attached to a specific message.

        This is the **adapter read access point**. Delegates to
        :meth:`LLMMessage.get_context`.

        :param int message_index: index of the target message (default ``-1``)
        :return: list of :class:`LLMContext` instances, or empty list
        :rtype: list[LLMContext]

        **Example**:

        .. code-block:: python

            for ctx in trace.get_context():
                print(ctx.text, ctx.score)
        """
        return self._get_message(message_index=message_index).get_context()

    def build_context(self, message_index: int = -1, metadata_fields: list = None) -> str:
        """
        Render context entries for a message into a text block suitable for
        injection into an LLM prompt.

        Delegates to :meth:`LLMMessage.build_context`.

        :param int message_index: index of the target message (default ``-1``)
        :param list metadata_fields: metadata key paths to include in ``<source>``
            tags, e.g. ``['system.document.source']``
        :return: rendered context string, empty string if no context
        :rtype: str

        **Example**:

        .. code-block:: python

            context = trace.build_context()
            if context:
                messages.append({"role": "assistant", "content": context})
        """
        if self.messages is None or len(self.messages) == 0:
            return ""
        return self._get_message(message_index=message_index).build_context(metadata_fields=metadata_fields)

    def to_json(self) -> dict:
        """
        Return the full trace as a dict.

        Returns ``_dict`` by reference (not a copy) so that nested
        entities (messages, context) can mutate in place.

        :return: trace dict
        :rtype: dict
        """
        return self._dict

    @classmethod
    def from_json(cls, json_data: dict, name: str = None) -> LLMTrace:
        """
        Build an LLMTrace from a dict.

        :param dict json_data: trace dict (must contain a ``messages`` list)
        :param str name: optional filename
        :return: LLMTrace instance
        :rtype: LLMTrace
        """
        cls._validate_dict(json_data=json_data)
        return cls(name=name, data_dict=json_data)

    @classmethod
    def from_item(cls, item: entities.Item) -> LLMTrace:
        """
        Load an LLMTrace from a platform Item.

        :param item: Dataloop Item (must be a JSON file containing a ``messages`` list)
        :return: LLMTrace instance
        :rtype: LLMTrace

        **Example**:

        .. code-block:: python

            item = dataset.items.get(filepath="/session.json")
            trace = dl.LLMTrace.from_item(item)
        """
        if 'json' not in item.mimetype or item.system.get('shebang', dict()).get('dltype') != 'llm_trace':
            raise ValueError('Expecting a JSON item with system.shebang.dltype = llm_trace')
        return cls(name=item.name, item=item)

    @classmethod
    def from_local_file(cls, filepath: str) -> LLMTrace:
        """
        Load an LLMTrace from a local JSON file.

        :param str filepath: path to the JSON file
        :return: LLMTrace instance
        :rtype: LLMTrace
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'File does not exist: {filepath}')
        if 'json' not in os.path.splitext(filepath)[-1]:
            raise ValueError(f'Expected a .json file, got {os.path.splitext(filepath)[-1]}')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_json(json_data=data, name=os.path.basename(filepath))

    def to_bytes_io(self) -> io.BytesIO:
        """
        Serialize the trace to a BytesIO buffer for upload.

        :return: BytesIO buffer
        :rtype: io.BytesIO
        """
        byte_io = io.BytesIO()
        byte_io.name = self.name
        byte_io.write(json.dumps(self.to_json()).encode())
        byte_io.seek(0)
        return byte_io

    def fetch(self):
        """
        Re-download the trace JSON from the platform and refresh ``_dict``.
        """
        if self._item is None:
            raise ValueError('Missing item, nothing to fetch.')
        items_repo = repositories.Items(client_api=client_api)
        items_repo._client_api.default_headers['x-dl-sanitize'] = '0'
        self._item = items_repo.get(item_id=self._item.id)
        trace_json = json.load(self._item.download(save_locally=False))
        self._validate_dict(json_data=trace_json)
        self._dict = trace_json
        self._dict.setdefault('shebang', 'dataloop')
        self._dict.setdefault('metadata', {}).setdefault('dltype', 'llm_trace')

    def update(self):
        """
        Push the current trace state back to the platform item.
        """
        if self._item is None:
            raise ValueError('Cannot update LLMTrace without an item.')
        self._item._Item__update_item_binary(_json=self.to_json())
        self._item = self._item.update()

    def __repr__(self):
        return f'<LLMTrace name={self.name!r} messages={len(self.messages)}>'
