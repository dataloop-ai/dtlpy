import datetime
import logging
import json
import time

import numpy as np

from .. import entities, exceptions

logger = logging.getLogger('dtlpy')


def prepare_dataset(dataset: entities.Dataset,
                    filters: entities.Filters = None,
                    partitions: dict = None,
                    async_clone: bool = False):
    """
    clones the given dataset and locks it to be readonly

    :param dataset:  `dl.Dataset` to clone
    :param dtlpy.entities.filters.Filters filters: `dl.Filters` to use when cloning - which items to clone
    :param partitions: dictionary to set partitions. key is partition name, value is the filter to set, eg.
                                    {dl.SnapshotPartitionType.TEST: dl.Filters(field='dir', values='/test')}
    :param async_clone: `bool` if True (default) - waits until the sync is complete
                                     False - return before the cloned dataset is fully populated
    :return: `dl.Dataset` which is readonly
    """

    project = dataset.project
    now = datetime.datetime.utcnow().isoformat(timespec='minutes', sep='T')  # This serves as an id
    today = datetime.datetime.utcnow().strftime('%F')

    # CLONE
    clone_name = 'cloned-{ds_name}-{date_str}'.format(ds_name=dataset.name, date_str=today)
    try:
        cloned_dataset = project.datasets.get(clone_name)
        logger.warning("Cloned dataset already exist. Using it...")
        return cloned_dataset
    except exceptions.NotFound:
        pass

    tic = time.time()
    cloned_dataset = dataset.clone(clone_name=clone_name,
                                   filters=filters)
    toc = time.time()
    logger.info("clone complete: {!r} in {:1.1f}[s]".format(cloned_dataset.name, toc - tic))

    assert cloned_dataset.name is not None, ('unable to get new ds {}'.format(clone_name))
    cloned_dataset.metadata['system']['clone_info'] = {'date': now,
                                                       'originalDatasetId': dataset.id,
                                                       }
    if filters is not None:
        cloned_dataset.metadata['system']['clone_info'].update({'filters': json.dumps(filters.prepare())})

    cloned_dataset._ontology_ids = dataset.ontology_ids
    cloned_dataset.update(system_metadata=True)

    # set partitions
    create_dataset_partition(dataset=dataset, partitions=partitions)

    # https://dataloop.atlassian.net/browse/DAT-13390
    # cloned_dataset.set_readonly(True)
    return cloned_dataset


def create_dataset_partition(dataset: entities.Dataset,
                             partitions: dict = None, ):
    """
    Creates a Partition of the given dataset to Train-Validation-Test  (dl.SnapshotPartition)
    :param dataset: dl.Dataset to preform the parition on
    :param partitions: `dict` {partition: filter}
        filter can be dl.Filter or a float (accumaliting to 1)
        partition needs to be one of dl.SnapshotPartition
    :return: None
    """


    has_partitions = dataset.get_partitions(list(entities.SnapshotPartitionType)).items_count > 0
    if has_partitions:
        logger.warning("Dataset {} ({!r}) already have Data Partitions".format(dataset.name, dataset.id))
    elif dataset.items_count > 200000:
        # FIXME: https://dataloop.atlassian.net/browse/DAT-18168
        err_msg = 'Set partition on large dataset is under construction. Current Dataset {ds_n!r} has {n_it} items\n'. \
            format(ds_n=dataset.name, n_it=dataset.items_count)
        err_msg += 'Please set the Partitions manually using smaller filters  Or advice with support@dataloop.ai'
        raise exceptions.SDKError(status_code=500, message=err_msg)

    # set partitions
    if partitions is None:
        partitions = {entities.SnapshotPartitionType.TRAIN: 0.8,
                      entities.SnapshotPartitionType.VALIDATION: 0.2,
                      entities.SnapshotPartitionType.TEST: 0.0}

    with_filters = all([isinstance(f, entities.Filters) for f in partitions.keys()])

    if not with_filters:
        # TODO need to replace with download all first and updating in bulks
        # not pages and not one by one
        dataset_item_ids = [item.id for item in dataset.items.get_all_items()]
        total_items = len(dataset_item_ids)
        np.random.seed(seed=int(time.time()))
        np.random.shuffle(dataset_item_ids)

    for partition, filters in partitions.items():
        if isinstance(filters, float):
            current_ids = [dataset_item_ids.pop() for _ in range(int(np.round(total_items * filters)))]
            filters = entities.Filters(field='id', values=current_ids, operator=entities.FiltersOperations.IN)
            dataset.set_partition(partition=partition, filters=filters)
        elif isinstance(filters, entities.Filters):
            dataset.set_partition(partition=partition, filters=filters)
        else:
            raise ValueError('unknown partition query type: {!}'.format(type(filters)))

    if dataset_item_ids is not None and len(dataset_item_ids) > 0:
        logger.warning('{} items left without partitions!'.format(len(dataset_item_ids)))
