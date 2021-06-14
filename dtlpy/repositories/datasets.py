"""
Datasets Repository
"""

import os
import tqdm
import logging
from urllib.parse import urlencode

from .. import entities, repositories, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Datasets:
    """
    Datasets repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Datasets repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def __get_from_cache(self) -> entities.Dataset:
        dataset = self._client_api.state_io.get('dataset')
        if dataset is not None:
            dataset = entities.Dataset.from_json(_json=dataset,
                                                 client_api=self._client_api,
                                                 datasets=self,
                                                 project=self._project)
        return dataset

    def __get_by_id(self, dataset_id) -> entities.Dataset:
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/datasets/{}'.format(dataset_id))
        if dataset_id is None or dataset_id == '':
            raise exceptions.PlatformException('400', 'Please checkout a dataset')

        if success:
            dataset = entities.Dataset.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 datasets=self,
                                                 project=self._project)
        else:
            raise exceptions.PlatformException(response)
        return dataset

    def __get_by_identifier(self, identifier=None) -> entities.Dataset:
        datasets = self.list()
        datasets_by_name = [dataset for dataset in datasets if identifier in dataset.name or identifier in dataset.id]
        if len(datasets_by_name) == 1:
            return datasets_by_name[0]
        elif len(datasets_by_name) > 1:
            raise Exception('Multiple datasets with this name exist')
        else:
            raise Exception("Dataset not found")

    def open_in_web(self, dataset_name=None, dataset_id=None, dataset=None):
        if dataset is None:
            dataset = self.get(dataset_id=dataset_id, dataset_name=dataset_name)
        self._client_api._open_in_web(resource_type='dataset',
                                      project_id=dataset.project.id,  # need to get the project otherwise will fail
                                      dataset_id=dataset.id)

    def checkout(self, identifier=None, dataset_name=None, dataset_id=None, dataset=None):
        """
        Check-out a project
        :param dataset:
        :param dataset_id:
        :param dataset_name:
        :param identifier: project name or partial id
        :return:
        """
        if dataset is None:
            if dataset_id is not None or dataset_name is not None:
                try:
                    dataset = self.project.datasets.get(dataset_name=dataset_name, dataset_id=dataset_id)
                except exceptions.MissingEntity:
                    dataset = self.get(dataset_id=dataset_id, dataset_name=dataset_name)
            elif identifier is not None:
                dataset = self.__get_by_identifier(identifier=identifier)
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Must provide partial/full id/name to checkout')
        self._client_api.state_io.put('dataset', dataset.to_json())
        logger.info('Checked out to dataset {}'.format(dataset.name))

    def list(self, name=None, creator=None) -> miscellaneous.List[entities.Dataset]:
        """
        List all datasets.

        :return: List of datasets
        """
        url = '/datasets'

        query_params = {
            'name': name,
            'creator': creator
        }

        if self._project is not None:
            query_params['projects'] = self.project.id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            pool = self._client_api.thread_pools('entity.create')
            datasets_json = response.json()
            jobs = [None for _ in range(len(datasets_json))]
            # return triggers list
            for i_dataset, dataset in enumerate(datasets_json):
                jobs[i_dataset] = pool.submit(entities.Dataset._protected_from_json,
                                              **{'client_api': self._client_api,
                                                 '_json': dataset,
                                                 'datasets': self,
                                                 'project': self.project})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            datasets = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            raise exceptions.PlatformException(response)
        return datasets

    def get(self, dataset_name=None, dataset_id=None, checkout=False, fetch=None) -> entities.Dataset:
        """
        Get dataset by name or id

        :param checkout:
        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Dataset object
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if dataset_id is None and dataset_name is None:
            dataset = self.__get_from_cache()
            if dataset is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Dataset was found, must checkout or provide an identifier in inputs')
        elif fetch:
            if dataset_id is not None and dataset_id != '':
                dataset = self.__get_by_id(dataset_id)
                # verify input dataset name is same as the given id
                if dataset_name is not None and dataset.name != dataset_name:
                    logger.warning(
                        "Mismatch found in datasets.get: dataset_name is different then dataset.name: "
                        "{!r} != {!r}".format(
                            dataset_name,
                            dataset.name))
            elif dataset_name is not None:
                datasets = self.list(name=dataset_name)
                if not datasets:
                    # empty list
                    raise exceptions.PlatformException('404', 'Dataset not found. Name: {!r}'.format(dataset_name))
                    # dataset = None
                elif len(datasets) > 1:
                    raise exceptions.PlatformException('400', 'More than one dataset with same name.')
                else:
                    dataset = datasets[0]
            else:
                raise exceptions.PlatformException(
                    error='404',
                    message='No input and no checked-out found')
        else:
            dataset = entities.Dataset.from_json(_json={'id': dataset_id,
                                                        'name': dataset_id},
                                                 client_api=self._client_api,
                                                 datasets=self,
                                                 project=self._project,
                                                 is_fetched=False)
        assert isinstance(dataset, entities.Dataset)
        if checkout:
            self.checkout(dataset=dataset)
        return dataset

    def delete(self, dataset_name=None, dataset_id=None, sure=False, really=False):
        """
        Delete a dataset forever!
        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param sure: are you sure you want to delete?
        :param really: really really?

        :return: True
        """
        if sure and really:
            dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/datasets/{}'.format(dataset.id))
            if not success:
                raise exceptions.PlatformException(response)
            logger.info('Dataset {!r} was deleted successfully'.format(dataset.name))
            return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete dataset from SDK. Please login to platform to delete')

    def update(self, dataset: entities.Dataset, system_metadata=False, patch: dict = None) -> entities.Dataset:
        """
        Update dataset field
        :param patch: Specific patch request
        :param dataset: Dataset entity
        :param system_metadata: bool
        :return: Dataset object
        """
        url_path = '/datasets/{}'.format(dataset.id)
        if system_metadata:
            url_path += '?system=true'

        if patch is None:
            patch = dataset.to_json()

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=patch)
        if success:
            logger.info('Dataset was updated successfully')
            return dataset
        else:
            raise exceptions.PlatformException(response)

    def directory_tree(self, dataset: entities.Dataset = None, dataset_name=None, dataset_id=None):
        """
        Get dataset's directory tree
        :return:
        """
        if dataset is None and dataset_name is None and dataset_id is None:
            raise exceptions.PlatformException('400', 'Must provide dataset, dataset name or dataset id')
        if dataset_id is None:
            if dataset is None:
                dataset = self.get(dataset_name=dataset_name)
            dataset_id = dataset.id

        url_path = '/datasets/{}/directoryTree'.format(dataset_id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)

        if success:
            return entities.DirectoryTree(_json=response.json())
        else:
            raise exceptions.PlatformException(response)

    def clone(self, dataset_id, clone_name, filters=None, with_items_annotations=True, with_metadata=True,
              with_task_annotations_status=True):
        """
        Clone a dataset

        :param dataset_id: to clone dataset
        :param clone_name: new dataset name
        :param filters: Filters entity or a query dict
        :param with_items_annotations:
        :param with_metadata:
        :param with_task_annotations_status:
        :return:
        """
        if filters is None:
            filters = entities.Filters().prepare()
        elif isinstance(filters, entities.Filters):
            filters = filters.prepare()
        else:
            raise exceptions.PlatformException(
                error='400',
                message='"filters" must be a dl.Filters entity. got: {!r}'.format(type(filters)))

        payload = {
            "name": clone_name,
            "filter": filters,
            "cloneDatasetParams": {
                "withItemsAnnotations": with_items_annotations,
                "withMetadata": with_metadata,
                "withTaskAnnotationsStatus": with_task_annotations_status
            }
        }
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/clone'.format(dataset_id),
                                                         json_req=payload)

        if not success:
            raise exceptions.PlatformException(response)

        command = entities.Command.from_json(_json=response.json(),
                                             client_api=self._client_api)
        command = command.wait()

        if 'returnedModelId' not in command.spec:
            raise exceptions.PlatformException(error='400',
                                               message="returnedModelId key is missing in command response: {!r}"
                                               .format(response))
        return self.get(dataset_id=command.spec['returnedModelId'])

    def merge(self, merge_name, dataset_ids, project_ids, with_items_annotations=True, with_metadata=True,
              with_task_annotations_status=True):
        payload = {
            "name": merge_name,
            "datasetsIds": dataset_ids,
            "projectIds": project_ids,
            "mergeDatasetParams": {
                "withItemsAnnotations": with_items_annotations,
                "withMetadata": with_metadata,
                "withTaskAnnotationsStatus": with_task_annotations_status
            }
        }
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/merge',
                                                         json_req=payload)

        if success:
            # TODO - support command entity
            return True
        else:
            raise exceptions.PlatformException(response)

    def sync(self, dataset_id):
        """
        Sync dataset with external storage

        :param dataset_id: to sync dataset
        :return:
        """

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/sync'.format(dataset_id))

        if success:
            # TODO - support command entity
            return True
        else:
            raise exceptions.PlatformException(response)

    def create(self,
               dataset_name,
               labels=None,
               attributes=None,
               ontology_ids=None,
               driver=None,
               driver_id=None,
               checkout=False) -> entities.Dataset:
        """
        Create a new dataset

        :param dataset_name: name
        :param labels: dictionary of {tag: color} or list of label entities
        :param attributes: dataset's ontology's attributes
        :param ontology_ids: optional - dataset ontology
        :param driver: optional - storage driver Driver object or driver name
        :param driver_id: optional - driver id
        :param checkout: bool. cache the dataset to work locally

        :return: Dataset object
        """
        # labels to list
        if labels is not None:
            if not all(isinstance(label, entities.Label) for label in labels):
                labels = entities.Dataset.serialize_labels(labels)
        else:
            labels = list()
        # get creator from token
        payload = {'name': dataset_name,
                   'projects': [self.project.id]}

        if driver_id is None and driver is not None:
            if isinstance(driver, entities.Driver):
                driver_id = driver.id
            elif isinstance(driver, str):
                driver_id = self.project.drivers.get(driver_name=driver).id
            else:
                raise exceptions.PlatformException(
                    error=400,
                    message='Input arg "driver" must be Driver object or a string driver name. got type: {!r}'.format(
                        type(driver)))
        if driver_id is not None:
            payload['driver'] = driver_id

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets',
                                                         json_req=payload)
        if success:
            dataset = entities.Dataset.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 datasets=self,
                                                 project=self.project)
            # create ontology and recipe
            dataset = dataset.recipes.create(ontology_ids=ontology_ids, labels=labels, attributes=attributes).dataset
            # # patch recipe to dataset
            # dataset = self.update(dataset=dataset, system_metadata=True)
        else:
            raise exceptions.PlatformException(response)
        logger.info('Dataset was created successfully. Dataset id: {!r}'.format(dataset.id))
        assert isinstance(dataset, entities.Dataset)
        if checkout:
            self.checkout(dataset=dataset)
        return dataset

    @staticmethod
    def _convert_single(downloader, item, img_filepath, local_path, overwrite, annotation_options,
                        annotation_filters, thickness, with_text, progress):
        # this is to convert the downloaded json files to any other annotation type
        try:
            downloader._download_img_annotations(item=item,
                                                 img_filepath=img_filepath,
                                                 local_path=local_path,
                                                 overwrite=overwrite,
                                                 annotation_options=annotation_options,
                                                 annotation_filters=annotation_filters,
                                                 thickness=thickness,
                                                 with_text=with_text)
        except Exception:
            logger.error('Failed to download annotation for item: {!r}'.format(item.name))
        progress.update()

    @staticmethod
    def download_annotations(dataset,
                             local_path=None,
                             filters: entities.Filters = None,
                             annotation_options: entities.ViewAnnotationOptions = None,
                             annotation_filters: entities.Filters = None,
                             annotation_filter_type: entities.AnnotationType = None,
                             annotation_filter_label=None,
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             remote_path=None):
        """
        Download dataset's annotations by filters.
        Filtering the dataset both for items and for annotations and download annotations
        Optional - also download annotations as: mask, instance, image mask of the item

        :param dataset: dataset to download from
        :param local_path: local folder or filename to save to.
        :param filters: Filters entity or a dictionary containing filters parameters
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param annotation_filters: Filters entity to filter annotations for download
        :param annotation_filter_type: DEPRECATED - list (dl.AnnotationType) of annotation types when downloading annotation, not relevant for JSON option
        :param annotation_filter_label: DEPRECATED - list of labels types when downloading annotation, not relevant for JSON option
        :param overwrite: optional - default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param remote_path: DEPRECATED and ignored
        :return: `List` of local_path per each downloaded item
        """
        if remote_path is not None:
            logger.warning(
                '"remote_path" is ignored. Use "filters=dl.Filters(field="dir, values={!r}"'.format(remote_path))
        if local_path is None:
            if dataset.project is None:
                # by dataset name
                local_path = os.path.join(
                    services.service_defaults.DATALOOP_PATH,
                    "datasets",
                    "{}_{}".format(dataset.name, dataset.id),
                )
            else:
                # by dataset and project name
                local_path = os.path.join(
                    services.service_defaults.DATALOOP_PATH,
                    "projects",
                    dataset.project.name,
                    "datasets",
                    dataset.name,
                )

        if annotation_filters is not None and \
                (annotation_filter_type is not None or annotation_filter_type is not None):
            # if BOTH deprecated and new args have values
            logger.warning(
                'Cannot input "annotation_filters" with one of "annotation_filter_type" or "annotation_filter_type". Using ONLY "annotation_filters"')
        elif annotation_filters is None and \
                (annotation_filter_type is not None or annotation_filter_type is not None):
            # if ONLY deprecated args have values
            annotation_filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
            if annotation_filter_type is not None:
                if not isinstance(annotation_filter_type, list):
                    annotation_filter_type = [annotation_filter_type]
                logger.warning(
                    'Deprecation Warning - input param "annotation_filter_type" will be deprecated starting from version "1.30.0". '
                    'Use "annotation_filters=dl.Filters(field={!r}, values={!r}, operator=entities.FiltersOperations.IN)"'.format(
                        'type',
                        annotation_filter_type))
                annotation_filters.add(field='type',
                                       values=annotation_filter_type,
                                       operator=entities.FiltersOperations.IN)

            if annotation_filter_label is not None:
                if not isinstance(annotation_filter_label, list):
                    annotation_filter_label = [annotation_filter_label]
                logger.warning(
                    'Deprecation Warning - input param "annotation_filter_label" will be deprecated starting from '
                    'version "1.30.0". Use "annotation_filters=dl.Filters(field={!r}, values={!r}, '
                    'operator=entities.FiltersOperations.IN)"'.format('label',
                                                                      annotation_filter_label))
                annotation_filters.add(field='label',
                                       values=annotation_filter_label,
                                       operator=entities.FiltersOperations.IN)

        if filters is None:
            filters = entities.Filters()
        if annotation_filters is not None:
            annotation_filters.resource = entities.FiltersResource.ANNOTATION
            filters.join = annotation_filters.prepare(query_only=True)

        downloader = repositories.Downloader(items_repository=dataset.items)
        downloader.download_annotations(dataset=dataset,
                                        filters=filters,
                                        annotation_filters=annotation_filters,
                                        local_path=local_path,
                                        overwrite=overwrite)
        if annotation_options is not None:
            pages = dataset.items.list(filters=filters)
            if not isinstance(annotation_options, list):
                annotation_options = [annotation_options]
            # convert all annotations to annotation_options
            pool = dataset._client_api.thread_pools(pool_name='dataset.download')
            jobs = [None for _ in range(pages.items_count)]
            progress = tqdm.tqdm(total=pages.items_count)
            for page in pages:
                for i_item, item in enumerate(page):
                    jobs[i_item] = pool.submit(
                        Datasets._convert_single,
                        **{
                            'downloader': downloader,
                            'item': item,
                            'img_filepath': None,
                            'local_path': local_path,
                            'overwrite': overwrite,
                            'annotation_options': annotation_options,
                            'annotation_filters': annotation_filters,
                            'thickness': thickness,
                            'with_text': with_text,
                            'progress': progress
                        }
                    )
            # get all results
            _ = [j.result() for j in jobs]
            progress.close()
        return local_path

    def set_readonly(self, state: bool, dataset: entities.Dataset):
        """
        Set dataset readonly mode
        :param state:
        :param dataset:
        :return:
        """
        if dataset.readonly != state:
            patch = {'readonly': state}
            self.update(dataset=dataset,
                        patch=patch)
            dataset._readonly = state
        else:
            logger.warning('Dataset is already "readonly={}". Nothing was done'.format(state))
