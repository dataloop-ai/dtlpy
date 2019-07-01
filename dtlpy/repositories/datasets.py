"""
Datasets Repository
"""

from multiprocessing.pool import ThreadPool
import logging
import traceback
from urllib.parse import urlencode
import numpy as np
from .. import entities, repositories, utilities, PlatformException, exceptions
import attr


@attr.s
class Datasets:
    """
    Datasets repository
    """
    client_api = attr.ib()
    project = attr.ib()
    logger = attr.ib(default=logging.getLogger('dataloop.repositories.datasets'))

    def list(self):
        """
        List all datasets.

        :return: List of datasets
        """
        if self.project is None:
            self.logger.exception('Cant list datasets with no project. Try same command from a "project" entity')
            raise ValueError('Cant list datasets with no project. Try same command from a "project" entity')
        query_string = urlencode({'name': '', 'creator': '', 'projects': self.project.id}, doseq=True)
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets?%s' % query_string)
        if success:
            datasets = utilities.List([entities.Dataset.from_json(client_api=self.client_api,
                                                                  _json=_json,
                                                                  project=self.project)
                                       for _json in response.json()])
        else:
            raise PlatformException(response)
        return datasets

    def get(self, dataset_name=None, dataset_id=None):
        """
        Get dataset by name or id

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :return: Dataset object
        """
        if dataset_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/datasets/%s' % dataset_id)
            if success:
                dataset = entities.Dataset.from_json(client_api=self.client_api,
                                                     _json=response.json(),
                                                     project=self.project)
            else:
                raise PlatformException(response)
        elif dataset_name is not None:
            datasets = self.list()
            dataset = [dataset for dataset in datasets if dataset.name == dataset_name]
            if not dataset:
                # empty list
                self.logger.info('Dataset not found. dataset_name: %s', dataset_name)
                raise PlatformException('404', 'Dataset not found.')
                # dataset = None
            elif len(dataset) > 1:
                # more than one dataset
                self.logger.warning('More than one dataset with same name. Please "get" by id')
                raise PlatformException('400', 'More than one dataset with same name.')
            else:
                dataset = dataset[0]
        else:
            self.logger.exception('Must choose by at least one. "dataset_id" or "dataset_name"')
            raise PlatformException('400', 'Must choose by at least one. "dataset_id" or "dataset_name"')
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
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/datasets/%s' % dataset.id)
            if not success:
                raise PlatformException(response)
            self.logger.info('Dataset was deleted successfully')
            return True
        else:
            raise PlatformException(error='403',
                                    message='Cant delete dataset from SDK. Please login to platform to delete')

    def update(self, dataset, system_metadata=False):
        """
        Update dataset field
        :param dataset: Dataset entity
        :param system_metadata: bool
        :return: Dataset object
        """
        url_path = '/datasets/%s' % dataset.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=dataset.to_json())
        if success:
            self.logger.info('Dataset was updated successfully')
            return dataset
        else:
            self.logger.exception('Platform error updating dataset. id: %s' % dataset.id)
            raise PlatformException(response)

    def create(self, dataset_name, labels=None, driver=None, attributes=None):
        """
        Create a new dataset

        :param dataset_name: name
        :param attributes:
        :param labels: dictionary of labels and colors
        :param driver: dictionary of labels and colors
        :return: Dataset object
        """
        # labels to list
        if labels is not None:
            labels = entities.Dataset.serialize_labels(labels)
        else:
            labels = list()
        # get creator from token
        if self.project is None:
            self.logger.exception('Cant create dataset with no project. Try same command from a "project" entity')
            raise ValueError('Cant create dataset with no project. Try same command from a "project" entity')
        payload = {'name': dataset_name,
                   'projects': [self.project.id]}
        if driver is not None:
            payload['driver'] = driver
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/datasets',
                                                        json_req=payload)
        if success:
            dataset = entities.Dataset.from_json(client_api=self.client_api,
                                                 _json=response.json(),
                                                 project=self.project)
            # create ontology and recipe
            recipe = dataset.recipes.create(ontology_ids=None, labels=labels, attributes=attributes)
            # patch recipe to dataset
            dataset = self.update(dataset=dataset, system_metadata=True)
        else:
            raise PlatformException(response)
        self.logger.info('Dataset was created successfully. Dataset id: %s' % dataset.id)
        return dataset

    def download_annotations(self, dataset, local_path, overwrite=False):
        downloader = repositories.Downloader(self)
        return downloader.download_annotations(dataset=dataset,
                                               local_path=local_path,
                                               overwrite=overwrite)

    def set_items_metadata(self, dataset_name=None, dataset_id=None, filters=None,
                           key_val_list=None, percent=None, random=True):
        """
        Set of metadata to post on items in filter.

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param filters: Filters entity or a dictionary containing filters parameters
        :param key_val_list: list of dictionary to set in metadata. e.g [{'split': 'training'}, {'split': 'validation'}
        :param percent: list of percentages to set the key_val_list
        :param random: bool. shuffle the items before setting the metadata
        :return: Output (list)
        """

        def set_single_item(i_item, item, key_val):
            try:
                metadata = item.to_json()
                for key, val in key_val.items():
                    metadata[key] = val
                item.from_dict(metadata)
                dataset.items.update(item)
                success[i_item] = True
            except Exception as err:
                success[i_item] = False
                errors[i_item] = '%s\n%s' % (err, traceback.format_exc())

        if key_val_list is None or percent is None:
            self.logger.exception('Must input name and percents')
            raise PlatformException('400', 'Must input name and percents')
        if not (isinstance(key_val_list, list) and isinstance(key_val_list[0], dict)):
            self.logger.exception(
                '"key_val" must be a list of dictionaries of keys and values to store in items metadata')
            raise PlatformException(
                error='400',
                message='"key_val" must be a list of dictionaries of keys and values to store in items metadata')
        if np.sum(percent) != 1:
            self.logger.exception('"percent" must sum up to 1')
            raise PlatformException('400', '"percent" must sum up to 1')
        # start
        dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
        pages = dataset.items.list(filters=filters)
        num_items = pages.items_count
        # get list of number of items for each percent
        percent_cumsum = num_items * np.cumsum(percent)
        # add zero at index 0
        percent_cumsum = np.insert(percent_cumsum, 0, 0).astype(int)
        if random:
            indices = np.random.permutation(num_items)
        else:
            indices = np.arange(num_items)
        splits = [indices[percent_cumsum[i]:percent_cumsum[i + 1]] for i in range(len(percent_cumsum) - 1)]
        success = [False for _ in range(pages.items_count)]
        output = [None for _ in range(pages.items_count)]
        errors = [None for _ in range(pages.items_count)]
        progress = Progress(max_val=num_items, progress_type='download')
        pool = ThreadPool(processes=32)
        progress.start()
        try:
            i_items = 0
            for page in pages:
                for item in page:
                    if item.type == 'dir':
                        success[i_items] = True
                        i_items += 1
                        continue
                    item_split_name = [key_val_list[i] for i, inds in enumerate(splits) if i_items in inds]
                    output[i_items] = item.id
                    pool.apply_async(set_single_item, kwds={'i_item': i_items,
                                                            'item': item,
                                                            'key_val_list': item_split_name})
                    i_items += 1
        except Exception as e:
            self.logger.exception(e)
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None,))
            progress.queue.join()
            progress.finish()
        # remove None items (dirs)
        success = [x for x in success if x is not None]
        output = [x for x in output if x is not None]
        good = success.count(True)
        bad = success.count(False)
        self.logger.info('Set metadata succefully for %d/%d' % (good, good + bad))
        # log error
        dummy = [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        # remove empty cells
        return output
