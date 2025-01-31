from .. import entities
from ..services.api_client import ApiClient
import attr

@attr.s
class Collection(entities.BaseEntity):
    """
    Represents a collection in the dataset.
    """

    # sdk
    _client_api = attr.ib(type=ApiClient, repr=False)

    key = attr.ib(type=str)
    name = attr.ib(type=str)

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Create a single Collection entity from the dataset JSON.

        :param _json: A dictionary containing collection data in the format:
                    { "metadata.system.collections.c0": {"name": "Justice League"} }
        :param client_api: The client API instance.
        :param is_fetched: Whether the entity was fetched from the platform.
        :return: A single Collection entity.
        """
        full_key, value = next(iter(_json.items()))
        # Strip the prefix
        key = full_key.replace("metadata.system.collections.", "")
        name = value.get("name")

        inst = cls(
            key=key,
            name=name,
            client_api=client_api,
        )
        inst.is_fetched = is_fetched
        return inst