from __future__ import annotations

import logging
from .. import entities, repositories
from ..services.api_client import client as client_api

logger = logging.getLogger(name='dtlpy')


class LLMContext(entities.DlEntity):
    """
    Represents a single retrieval result attached to a message in an LLM trace.

    Uses a single internal ``_dict`` dict as the source of truth.
    Known fields (``text``, ``item_id``, ``score``, ``filename``) are exposed
    via DlProperty descriptors; any additional fields live directly in ``_dict``.

    :param str text: The retrieved text content (optional if ``item_id`` is set)
    :param str item_id: Dataloop Item ID of the source document (optional if ``text`` is set)
    :param float score: Relevance score between 0 and 1 (optional)
    :param str filename: Human-readable source filename (optional)
    :param kwargs: Arbitrary extra fields stored in the context body

    **Example**:

    .. code-block:: python

        ctx = dl.LLMContext(text="Deep Research is a new capability...",
                            item_id="64a7f...",
                            filename="report.pdf",
                            score=0.98)
        trace.add_context([ctx])
    """

    text: str = entities.DlProperty(location=['text'], _type=str)
    item_id: str = entities.DlProperty(location=['item_id'], _type=str)
    score: float = entities.DlProperty(location=['score'])
    filename: str = entities.DlProperty(location=['filename'], _type=str)

    @staticmethod
    def _validate_dict(json_data: dict):
        """Raise if *json_data* lacks both ``text`` and ``item_id``."""
        if not isinstance(json_data, dict):
            raise ValueError(f"Expected dict, got {type(json_data)}")
        if json_data.get('text') is None and json_data.get('item_id') is None:
            raise ValueError("LLMContext requires at least one of 'text' or 'item_id'")

    def __init__(self, data_dict=None, **kwargs):
        data_dict = self._split_kwargs(data_dict=data_dict, kwargs=kwargs)
        super().__init__(_dict=data_dict, **kwargs)
        self._validate_dict(json_data=self._dict)

    def to_json(self) -> dict:
        """
        Return the context entry as a plain dict.

        Returns ``_dict`` by reference (not a copy) so that mutations
        propagate back to the parent message's context list.

        :return: context dict
        :rtype: dict
        """
        return self._dict

    @classmethod
    def from_json(cls, json_data: dict) -> LLMContext:
        """
        Create an LLMContext from a dict.

        :param dict json_data: context dict (must include at least one of ``text`` or ``item_id``)
        :return: LLMContext instance
        :rtype: LLMContext
        """
        cls._validate_dict(json_data=json_data)
        return cls(data_dict=json_data)

    def resolve_text(self, metadata_fields: list = None):
        """
        Resolve text content and source metadata for this context entry.

        If :attr:`text` is ``None`` but :attr:`item_id` is set, the text is
        fetched from the platform item.  Metadata paths are extracted from
        the platform Item's metadata (matching :meth:`PromptItem.build_context`
        behaviour), so an ``item_id`` is required for metadata extraction.

        :param list metadata_fields: dot-separated key paths into the platform
            Item's ``metadata`` dict.  Each path is walked segment by segment
            (e.g. ``'system.document.source'`` traverses
            ``item.metadata['system']['document']['source']``).  The last
            segment is used as the label in the output string
            (``source:<value>``).  If any segment along the way is missing or
            not a dict, the value defaults to an empty string.
            Requires ``item_id`` — when no ``item_id`` is set, metadata
            extraction is skipped entirely because there is no platform Item
            to read metadata from.
        :return: tuple of (resolved text, formatted source-parts string)
        :rtype: tuple[str, str]
        """
        if metadata_fields is None:
            metadata_fields = []

        text = self.text
        context_item = None
        if self.item_id:
            items_repo = repositories.Items(client_api=client_api)
            items_repo._client_api.default_headers['x-dl-sanitize'] = '0'
            context_item = items_repo.get(item_id=self.item_id)
            if text is None:
                buf = context_item.download(save_locally=False)
                text = buf.read().decode(encoding='utf-8')

        # Metadata is extracted from the platform Item's metadata dict,
        # so when no item_id is provided we skip metadata extraction entirely.
        source_parts = ""
        if context_item is not None:
            for path in metadata_fields:
                # path is a dot-separated path in the nearest item metadata
                key = path.split('.')[-1]
                value = context_item.metadata
                for part in path.split('.'):
                    if not isinstance(value, dict):
                        value = ""
                        break
                    value = value.get(part, "")
                source_parts += f"{key}:{value}\n"

        if self.filename:
            source_parts += f"filename:{self.filename}\n"

        return text, source_parts

    def __repr__(self):
        return f'<LLMContext item_id={self.item_id!r} score={self.score}>'
