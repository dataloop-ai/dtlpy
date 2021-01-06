"""
Datasets Repository
"""

import os
import tqdm
import logging
from urllib.parse import urlencode
from multiprocessing.pool import ThreadPool

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
                jobs[i_dataset] = pool.apply_async(entities.Dataset._protected_from_json,
                                                   kwds={'client_api': self._client_api,
                                                         '_json': dataset,
                                                         'datasets': self,
                                                         'project': self.project})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all results
            results = [j.get() for j in jobs]
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
            elif dataset_name is not None:
                datasets = self.list(name=dataset_name)
                if not datasets:
                    # empty list
                    raise exceptions.PlatformException('404', 'Dataset not found. Name: {}'.format(dataset_name))
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
            logger.info('Dataset {} was deleted successfully'.format(dataset.name))
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
                message='"filters" must be a dl.Filters entity. got: {}'.format(type(filters)))

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

        if success:
            return entities.Dataset.from_json(_json=response.json(),
                                              project=self._project,
                                              datasets=self,
                                              client_api=self._client_api)
        else:
            raise exceptions.PlatformException(response)

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
            return entities.Dataset.from_json(_json=response.json(),
                                              project=self._project,
                                              datasets=self,
                                              client_api=self._client_api)
        else:
            raise exceptions.PlatformException(response)

    def create(self, dataset_name, labels=None, driver=None, attributes=None, ontology_ids=None,
               checkout=False) -> entities.Dataset:
        """
        Create a new dataset

        :param checkout:
        :param ontology_ids: optional - dataset ontology
        :param dataset_name: name
        :param attributes: dataset's ontology's attributes
        :param labels: dictionary of {tag: color} or list of label entities
        :param driver: optional
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
        if driver is not None:
            payload['driver'] = driver
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
        logger.info('Dataset was created successfully. Dataset id: {}'.format(dataset.id))
        assert isinstance(dataset, entities.Dataset)
        if checkout:
            self.checkout(dataset=dataset)
        return dataset

    @staticmethod
    def download_annotations(dataset,
                             local_path=None,
                             filters=None,
                             annotation_options: entities.ViewAnnotationOptions = None,
                             annotation_filter_type=None,
                             annotation_filter_label=None,
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             num_workers=32,
                             remote_path=None):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param dataset: dataset to download from
        :param local_path: local folder or filename to save to.
        :param filters: Filters entity or a dictionary containing filters parameters
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param annotation_filter_type: list of annotation types when downloading annotation,
                                                                                        not relevant for JSON option
        :param annotation_filter_label: list of labels types when downloading annotation, not relevant for JSON option
        :param overwrite: optional - default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param remote_path optinal - remote path to download
        :param num_workers number of threads
        :return: `List` of local_path per each downloaded item
        """

        def download_single(i_item, i_img_filepath, i_local_path, i_overwrite, i_annotation_options,
                            i_annotation_filter_type, i_annotation_filter_label, i_thickness, i_with_text):
            try:
                repositories.Downloader._download_img_annotations(item=i_item,
                                                                  img_filepath=i_img_filepath,
                                                                  local_path=i_local_path,
                                                                  overwrite=i_overwrite,
                                                                  annotation_options=i_annotation_options,
                                                                  annotation_filter_type=i_annotation_filter_type,
                                                                  annotation_filter_label=i_annotation_filter_label,
                                                                  thickness=i_thickness,
                                                                  with_text=i_with_text)
            except Exception:
                logger.error('Failed to download annotation for item: {}'.format(item.name))

            progress.update(1)

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

        downloader = repositories.Downloader(items_repository=dataset.items)

        # check if need to only download zip
        if filters is None:
            filters = entities.Filters()
            if annotation_options is None:
                downloader.download_annotations(dataset=dataset,
                                                local_path=local_path,
                                                overwrite=overwrite,
                                                remote_path=remote_path)
                return local_path

        filters.add(field='annotated', values=True)

        if annotation_options is None:
            annotation_options = [entities.ViewAnnotationOptions.JSON]
        if not isinstance(annotation_options, list):
            annotation_options = [annotation_options]

        if annotation_filter_type is not None or annotation_filter_label is not None:
            if filters is None:
                filters = entities.Filters(resource=entities.FiltersResource.ITEM)
            filters.add(field='annotated', values=True)

        if annotation_filter_type is not None:
            if not isinstance(annotation_filter_type, list):
                annotation_filter_type = [annotation_filter_type]
            filters.add_join(field='type', values=annotation_filter_type, operator=entities.FiltersOperations.IN)

        if annotation_filter_label is not None:
            if not isinstance(annotation_filter_label, list):
                annotation_filter_label = [annotation_filter_label]
            filters.add_join(field='label', values=annotation_filter_label, operator=entities.FiltersOperations.IN)

        pages = dataset.items.list(filters=filters)

        if pages.items_count > dataset.annotated / 10:
            downloader.download_annotations(dataset=dataset,
                                            local_path=local_path,
                                            overwrite=overwrite,
                                            remote_path=remote_path)

        pool = ThreadPool(processes=num_workers)
        progress = tqdm.tqdm(total=pages.items_count)
        for page in pages:
            for item in page:
                pool.apply_async(
                    func=download_single,
                    kwds={
                        'i_item': item,
                        'i_img_filepath': None,
                        'i_local_path': local_path,
                        'i_overwrite': overwrite,
                        'i_annotation_options': annotation_options,
                        'i_annotation_filter_type': annotation_filter_type,
                        'i_annotation_filter_label': annotation_filter_label,
                        'i_thickness': thickness,
                        'i_with_text': with_text
                    }
                )

        pool.close()
        pool.join()
        pool.terminate()
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
