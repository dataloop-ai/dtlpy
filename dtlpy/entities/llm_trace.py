from __future__ import annotations

import logging
import json
import io
import os
import time
from typing import List, Union, Optional, Iterator

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

    def stream_response(
        self,
        stream: Iterator[str],
        dataset: entities.Dataset = None,
        role: str = "assistant",
        model_info: dict = None,
        update_interval: float = 2.0,
    ) -> str:
        """
        Consume a streaming LLM response, pushing intermediate text via
        a lightweight ``FreeText`` annotation and only calling
        :meth:`update` once when the stream finishes.

        If the trace has not been uploaded yet (no underlying item),
        provide a *dataset* and the trace will be uploaded automatically
        before streaming begins.

        During iteration a ``FreeText`` annotation is created on the
        underlying item and updated every *update_interval* seconds so
        that consumers (e.g. the UI) can display partial results without
        the cost of a full trace update.  When the stream is exhausted
        the annotation is removed, the complete message is added to the
        trace, and :meth:`update` is called exactly once.

        :param stream: an iterator that yields text chunks (strings)
        :param dataset: optional :class:`Dataset` used to upload the
            trace when it has no item yet
        :param str role: message role (default ``"assistant"``)
        :param dict model_info: optional dict attached to the message
            (e.g. ``{'name': 'gpt-4o', 'confidence': 1.0, 'model_id': '...'}``).
        :param float update_interval: minimum seconds between annotation
            updates (default ``2.0``)
        :return: the fully accumulated response text
        :rtype: str

        **Example**:

        .. code-block:: python

            stream = openai_client.chat.completions.create(stream=True, ...)
            response = trace.stream_response(
                stream=(chunk.choices[0].delta.content or "" for chunk in stream),
                dataset=dataset,
                model_info={'name': 'gpt-4o', 'confidence': 1.0, 'model_id': model.id},
                update_interval=2.0,
            )
        """
        logger.info("stream_response started for trace %r", self.name)
        if self._item is None:
            if dataset is None:
                raise ValueError("Cannot stream without an item. Provide a dataset to auto-upload the trace.")
            self._item = dataset.items.upload(local_path=self, overwrite=True)
            logger.info("Trace auto-uploaded as item %s", self._item.id)

        # Create a streaming annotation on the item
        builder = self._item.annotations.builder()
        builder.add(
            annotation_definition=entities.FreeText(label="streaming", text=""),
            model_info=model_info or {"confidence": 0.0},
        )
        streaming_annotation = builder.upload()[0]

        response = ""
        last_update = time.time()
        logger.info("Starting to stream response for trace %r", self.name)
        for chunk in stream:
            response += chunk
            now = time.time()
            if now - last_update >= update_interval:
                streaming_annotation.annotation_definition = entities.FreeText(
                    label=streaming_annotation.label,
                    text=response,
                )
                try:
                    streaming_annotation = streaming_annotation.update()
                except Exception:
                    logger.warning("Failed to update streaming annotation", exc_info=True)
                last_update = now
        
        logger.info("Finished streaming response for trace %r", self.name)
        logger.info("Added final message to trace %r", self.name)
        # Add the final message to the trace and push once
        msg = LLMMessage(
            role=role,
            content=response,
            **({"model_info": model_info} if model_info else {}),
        )
        self.add_message(msg)
        self.update()

        # Remove the temporary streaming annotation
        try:
            streaming_annotation.delete()
        except Exception:
            logger.warning("Failed to delete streaming annotation", exc_info=True)

        logger.info("stream_response completed for trace %r, response length: %d", self.name, len(response))
        return response

    def __repr__(self):
        return f'<LLMTrace name={self.name!r} messages={len(self.messages)}>'
