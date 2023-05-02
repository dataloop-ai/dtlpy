import datetime
import logging
import json
import time

import numpy as np

from .. import entities, exceptions

logger = logging.getLogger(name='dtlpy')


def prepare_dataset(dataset: entities.Dataset,
                    subsets: dict,
                    filters: entities.Filters = None,
                    async_clone: bool = False):
    """
    clones the given dataset and locks it to be readonly

    :param dataset:  `dl.Dataset` to clone
    :param dtlpy.entities.filters.Filters filters: `dl.Filters` to use when cloning - which items to clone
    :param subsets: dictionary to set subsets from the data.
                        key is subset name, value is the filter to set, eg.
                                    {dl.DatasetSubsetType.TEST: dl.Filters(field='dir', values='/test')}
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

    orig_recipe = dataset.recipes.list()[0]
    cloned_recipe = orig_recipe.clone(shallow=True)
    cloned_dataset.metadata['system']['recipes'] = [cloned_recipe.id]

    logger.info("clone complete: {!r} in {:1.1f}[s]".format(cloned_dataset.name, toc - tic))

    assert cloned_dataset.name is not None, ('unable to get new ds {}'.format(clone_name))
    cloned_dataset.metadata['system']['clone_info'] = {'date': now,
                                                       'originalDatasetId': dataset.id}
    if filters is not None:
        cloned_dataset.metadata['system']['clone_info'].update({'filters': json.dumps(filters.prepare())})
    cloned_dataset.update(system_metadata=True)
    return cloned_dataset
    # cloned_dataset.set_readonly(True)
