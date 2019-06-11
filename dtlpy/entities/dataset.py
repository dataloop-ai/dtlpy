import os
import logging
import attr

from .. import repositories, utilities
logger = logging.getLogger('dataloop.dataset')

@attr.s
class Dataset:
    """
    Dataset object
    """
    client_api = attr.ib()
    id = attr.ib()
    url = attr.ib()
    name = attr.ib()
    annotated = attr.ib()
    creator = attr.ib()
    projects = attr.ib()
    itemsCount = attr.ib()
    metadata = attr.ib()
    items_url = attr.ib()
    directoryTree = attr.ib()
    export = attr.ib()

    # entities
    project = attr.ib()

    # repositories
    _items = attr.ib()
    _recipes = attr.ib()

    # defaults
    ontology_ids = attr.ib()
    labels = attr.ib()

    @classmethod
    def from_json(cls, project, _json, client_api):
        """
        Build a Dataset entity object from a json

        :param _json: _json respons form host
        :param project: dataset's project
        :param client_api: client_api
        :return: Dataset object
        """
        if 'metadata' in _json:
            metadata = _json['metadata']
        else:
            metadata = None

        return cls(
            client_api=client_api,
            annotated=_json['annotated'],
            creator=_json['creator'],
            directoryTree=_json['directoryTree'],
            export=_json['export'],
            id=_json['id'],
            items_url=_json['items'],
            itemsCount=_json['itemsCount'],
            name=_json['name'],
            projects=_json['projects'],
            url=_json['url'],
            project=project,
            metadata=metadata)

    @_items.default
    def set_items(self):
        return repositories.Items(dataset=self, client_api=self.client_api)

    @ontology_ids.default
    def set_ontology_ids(self):
        ontlogy_ids = list()
        if self.metadata is not None and 'system' in self.metadata and 'recipes' in self.metadata['system']:
            recipe_ids = self.get_recipe_ids()
            recipes = list()
            for rec_id in recipe_ids:
                recipes.append(self.recipes.get(recipe_id=rec_id))

            ontologies = dict()
            for recipe in recipes:
                ontologies[recipe.id] = recipe.ontologyIds
            self.ontology_ids = ontologies
        return ontlogy_ids

    @property
    def items(self):
        assert isinstance(self._items, repositories.Items)
        return self._items

    @_recipes.default
    def set_recipes(self):
        return repositories.Recipes(dataset=self, client_api=self.client_api)

    @property
    def recipes(self):
        assert isinstance(self._recipes, repositories.Recipes)
        return self._recipes

    def __copy__(self):
        return Dataset.from_json(_json=self.to_json(), project=self.project, client_api=self.client_api)

    @labels.default
    def set_labels(self):
        if self.metadata is None:
            return list()
        labels = list()
        recipes = self.recipes.list()
        for rec in recipes:
            for ont in rec.ontologies.list():
                labels += ont.labels
        return labels

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Dataset)._items,
                                                              attr.fields(Dataset).items_url,
                                                              attr.fields(Dataset).project,
                                                              attr.fields(Dataset)._recipes,
                                                              attr.fields(Dataset).client_api))
        _json.update({'items': self.items_url})
        return _json

    def __get_local_path__(self):
        if self.project is not None:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'projects', self.project.name,
                                      'datasets', self.name)
        else:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'datasets', '%s_%s' % (self.name, self.id))
        return local_path

    def print(self):
        utilities.List([self]).print()

    @staticmethod
    def serialize_labels(labels_dict):
        """
        Convert hex color format to rgb

        :param labels_dict: dict of labels
        :return: dict of converted labels
        """
        dataset_labels_dict = dict()
        for label, color in labels_dict.items():
            dataset_labels_dict[label] = '#%02x%02x%02x' % color
        return dataset_labels_dict

    def get_recipe_ids(self):
        """
        Get dataset recipe Ids

        :return: list of recipe ids
        """
        return self.metadata['system']['recipes']

    def download_annotations(self, local_path=None):
        """
        Download annotations json for entire dataset

        :param local_path: optional - local directory in which annotations will be saved
        :return:
        """
        return self.project.datasets.download_annotations(dataset_id=self.id, local_path=local_path)

    def download(self, query=None, local_path=None, filetypes=None,
                 num_workers=None, download_options=None, save_locally=True,
                 download_item=True, annotation_options=None,
                 opacity=1, with_text=False, thickness=3):
        """
        Download dataset by query.
        Quering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item
        :param query: Query entity or a dictionary containing query parameters
        :param local_path: local folder or filename to save to. if folder ends with * images with be downloaded directly
        to folder. else - an "images" folder will be create for the images
        :param filetypes: a list of filetype to download. e.g ['.jpg', '.png']
        :param num_workers: default - 32
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param save_locally: bool. save to disk or return a buffer
        :param download_item: bool. download image
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param opacity: for img_mask
        :param with_text: add label to annotations
        :param thickness: annotation line
        :return:
        """
        return self.project.datasets.download(dataset_id=self.id,
                                              query=query, local_path=local_path, filetypes=filetypes,
                                              num_workers=num_workers, download_options=download_options,
                                              save_locally=save_locally,
                                              download_item=download_item, annotation_options=annotation_options,
                                              opacity=opacity, with_text=with_text, thickness=thickness)

    def upload(self, local_path=None, local_annotations_path=None, remote_path=None,
               upload_options=None, filetypes=None, num_workers=None):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param local_path: local files to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        annotations need to be in same files structure as "local_path"
        :param remote_path: remote path to save.
        :param upload_options: 'merge' or 'overwrite'
        :param filetypes: list of filetype to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers: num_workers
        :return:
        """
        return self.project.datasets.upload(dataset_id=self.id,
                                            local_path=local_path, local_annotations_path=local_annotations_path,
                                            remote_path=remote_path,
                                            upload_options=upload_options, filetypes=filetypes, num_workers=num_workers)

    def delete(self, sure=False, really=False):
        """
        Delete a dataset forever!
        :param sure: are you sure you want to delete?
        :param really: really really?
        :return:
        """
        return self.project.datasets.delete(dataset_id=self.id,
                                            sure=sure,
                                            really=really)

    def update(self, system_metadata=False):
        """
        Update dataset field
        :param system_metadata: bool - True, if you want to change metadata system
        :return:
        """
        return self.project.datasets.update(dataset=self, system_metadata=system_metadata)
