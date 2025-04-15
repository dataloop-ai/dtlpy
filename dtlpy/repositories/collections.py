from .. import entities, exceptions
from ..services.api_client import ApiClient
from typing import List

class Collections:
    def __init__(self, 
                client_api: ApiClient,
                item: entities.Item = None, 
                dataset: entities.Dataset = None
            ):
        self._client_api = client_api
        self._dataset = dataset
        self._item = item

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            raise ValueError("Must set dataset for this action.")
        return self._dataset
    
    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        self._dataset = dataset

    @property
    def item(self) -> entities.Item:
        if self._item is None:
            raise ValueError("Must set item for this action.")
        return self._item
    
    @item.setter
    def item(self, item: entities.Item):
        self._item = item
    
    def create(self, name: str) -> entities.Collection:
        """
        Creates a new collection in the dataset.

        :param name: The name of the new collection.
        :return: The created collection details.
        """
        self.validate_max_collections()
        self.validate_collection_name(name)
        payload = {"name": name}
        success, response = self._client_api.gen_request(
            req_type="post", path=f"/datasets/{self.dataset.id}/items/collections", json_req=payload
        )
        if success:
            collection_json = self._single_collection(data=response.json(), name=name)
            return entities.Collection.from_json(client_api=self._client_api, _json=collection_json)
        else:
            raise exceptions.PlatformException(response) 

    def update(self, collection_name: str, new_name: str) -> entities.Collection:
        """
        Updates the name of an existing collection.

        :param collection_id: The ID of the collection to update.
        :param new_name: The new name for the collection.
        :return: The updated collection details.
        """
        self.validate_collection_name(new_name)
        payload = {"name": new_name}
        success, response = self._client_api.gen_request(
            req_type="patch", path=f"/datasets/{self.dataset.id}/items/collections/{collection_name}", json_req=payload
        )
        if success:
            collection_json = self._single_collection(data=response.json(), name=new_name)
            return entities.Collection.from_json(client_api=self._client_api, _json=collection_json)
        else:
            raise exceptions.PlatformException(response)

    def delete(self, collection_name: str) -> bool:
        """
        Deletes a collection from the dataset.

        :param collection_name: The name of the collection to delete.
        """
        success, response = self._client_api.gen_request(
            req_type="delete", path=f"/datasets/{self.dataset.id}/items/collections/{collection_name}"
        )
        if success:
            # Wait for the split operation to complete
            command = entities.Command.from_json(_json=response.json(),
                                                client_api=self._client_api)
            command.wait()
            return True
        else:
            raise exceptions.PlatformException(response)

    def clone(self, collection_name: str) -> entities.Collection:
        """
        Clones an existing collection, creating a new one with a unique name.

        :param collection_name: The name of the collection to clone.
        :return: The cloned collection details as a dictionary.
        """
        self.validate_max_collections()
        collections = self.list_all_collections()
        original_collection = next((c for c in collections if c["name"] == collection_name), None)

        if not original_collection:
            raise ValueError(f"Collection with name '{collection_name}' not found.")

        source_name = original_collection["name"]
        num = 0
        clone_name = ""
        while True:
            num += 1
            clone_name = f"{source_name}-clone-{num}"
            if not any(c["name"] == clone_name for c in collections):  # Use c["name"] for comparison
                break

        # Create the cloned collection
        cloned_collection = self.create(name=clone_name)
        filters = entities.Filters()
        filters.add(field=f'metadata.system.collections.{original_collection["key"]}', values=True)
        self.assign(collections=[cloned_collection.name], 
                    filters=filters)
        return cloned_collection


    def list_all_collections(self) -> entities.Collection:
        """
        Retrieves all collections in the dataset.

        :return: A list of collections in the dataset.
        """
        success, response = self._client_api.gen_request(
            req_type="GET", path=f"/datasets/{self.dataset.id}/items/collections"
        )
        if success:
            data = response.json()
            return self._list_collections(data)
        else:
            raise exceptions.PlatformException(response)
        
    def validate_collection_name(self, name: str):
        """
        Validate that the collection name is unique.

        :param name: The name of the collection to validate.
        :raises ValueError: If a collection with the same name already exists.
        """
        collections = self.list_all_collections()
        if any(c["name"] == name for c in collections): 
            raise ValueError(f"A collection with the name '{name}' already exists.")

    def validate_max_collections(self) -> None:
        """
        Validates that the dataset has not exceeded the maximum allowed collections.

        :raises ValueError: If the dataset has 10 or more collections.
        """
        collections = self.list_all_collections()
        if len(collections) >= 10:
            raise ValueError("The dataset already has the maximum number of collections (10).")
        
    def list_missing_collections(self) -> List[str]:
        """
        List all items in the dataset that are not assigned to any collection.

        :return: A list of item IDs that are not part of any collection.
        """
        filters = entities.Filters()
        filters.add(field='metadata.system.collections', values=None)
        filters.add(field='datasetId', values=self._dataset.id)
        return self._dataset.items.list(filters=filters)
    
    def list_unassigned_items(self) -> list:
        """
        List unassigned items in a dataset (items where all collection fields are false).

        :return: List of unassigned item IDs
        :rtype: list
        """
        filters = entities.Filters(method=entities.FiltersMethod.AND)  # Use AND method for all conditions
        collection_fields = [
            "collections0",
            "collections1",
            "collections2",
            "collections3",
            "collections4",
            "collections5",
            "collections6",
            "collections7",
            "collections8",
            "collections9",
        ]

        # Add each field to the filter with a value of False
        for field in collection_fields:
            filters.add(field=field, values=False, method=entities.FiltersMethod.AND)

        missing_ids = []
        pages = self._dataset.items.list(filters=filters)
        for page in pages:
            for item in page:
                # Items that pass filters mean all collections are false
                missing_ids.append(item.id)

        return missing_ids

    def assign(
        self, 
        collections: List[str],
        dataset_id: str = None, 
        item_id: str = None, 
        filters: entities.Filters = None
    ) -> bool:
        """
        Assign an item to a collection. Creates the collection if it does not exist.

        :param collections: List of the collections to assign the item to.
        :param dataset_id: ID of the dataset.
        :param item_id: (Optional) ID of the item to assign. If not provided, all items in the dataset will be updated.
        :param filters: (Optional) Filters of items to assign to the collections.
        :return: True if the assignment was successful, otherwise raises an exception.
        """
        if not isinstance(collections, list):
            raise ValueError("collections must be a list.")
        if dataset_id is None and self._dataset is not None:
            dataset_id = self.dataset.id
        if item_id is None and self._item is not None:
            item_id = self.item.id 
        # Build the query structure
        if item_id is not None:
            query = {
                "id": {"$eq": item_id}
            }
        elif filters is not None:
            query = filters.prepare().get("filter")
        else:
            raise ValueError("Either collection_key or item_id must be provided.")

        # Create the payload
        payload = {
            "query": query,
            "collections": collections,
        }

        # Make the API request to assign the item
        success, response = self._client_api.gen_request(
            req_type="post",
            path=f"/datasets/{dataset_id}/items/collections/bulk-add",
            json_req=payload,
        )

        if success:
            # Wait for the operation to complete
            command = entities.Command.from_json(_json=response.json(), client_api=self._client_api)
            command.wait()
            return True
        else:
            raise exceptions.PlatformException(f"Failed to assign item to collections: {response}")

        
    def unassign(self, 
                 collections: List[str], 
                 dataset_id: str = None,
                 item_id: str = None, 
                 filters: entities.Filters = None) -> bool:
        """
        Unassign an item from a collection.
        :param collections: List of collection names to unassign.
        :param dataset_id: ID of the dataset.
        :param item_id: ID of the item.
        :param filters: (Optional) Filters of items to unassign from the collections.
        """
        if not isinstance(collections, list):
            raise ValueError("collections must be a list.")
        # build the context
        if dataset_id is None and self._dataset is not None:
            dataset_id = self._dataset.id
        if item_id is None and self._item is not None:
            item_id = self._item.id
            
        # build the payload
        if item_id is not None and filters is None:
            payload = {
                "query": {"id": {"$eq": item_id}},
                "collections": collections,
            }
        elif filters is not None and item_id is None:
            payload = {
                "query": filters.prepare().get("filter"),
                "collections": collections,
            }
        else:
            raise ValueError("Either item_id or filters must be provided but not both.")
        success, response = self._client_api.gen_request(
            req_type="post",
            path=f"/datasets/{dataset_id}/items/collections/bulk-remove",
            json_req=payload,
        )
        if success:
            # Wait for the split operation to complete
            command = entities.Command.from_json(_json=response.json(),
                                                client_api=self._client_api)
            command.wait()
            return True
        else:
            raise exceptions.PlatformException(response)

    def _single_collection(sef, data: dict, name: str):
        """
        Retrieves the key-value pair from the dictionary where the collection's name matches the given name.

        :param data: A dictionary containing collection data in the format:
                    { "metadata.system.collections.c0": {"name": "Justice League"}, ... }
        :param name: The name of the collection to find.
        :return: The key-value pair where the name matches, or None if not found.
        """
        for key, value in data.items():
            if value.get("name") == name:
                return {key: value}
        return None
    
    def _list_collections(self, data: dict):
        """
        Create a list of Collection entities from the dataset JSON.

        :param data: The flat JSON containing collection data in the format:
                    { "metadata.system.collections.c0": {"name": "Justice League"}, ... }
        :return: A list of Collection entities.
        """
        collections = []
        for full_key, value in data.items():
            if "metadata.system.collections" in full_key:
                # Strip the prefix
                key = full_key.replace("metadata.system.collections.", "")
                collection_name = value.get("name")
                collections.append({"key": key, "name": collection_name})
        return collections
    
    def get_name_by_key(self, key: str) -> str:
        """
        Get the name of a collection by its key.

        :param key: The key of the collection (e.g., 'c0', 'c1').
        :return: The name of the collection if it exists; otherwise, an empty string.
        """
        # Assuming collections is a list of dictionaries
        collections = self.list_all_collections()
        for collection in collections:
            if collection.get("key") == key:
                return collection.get("name", "")
        return ""