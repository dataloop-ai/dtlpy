import sys

import pandas as pd
import numpy as np
import traceback
import datetime
import logging
import tqdm
import uuid
import os

from .. import entities
from . import BaseModelAdapter, metrics

logger = logging.getLogger(name='dtlpy')


def mean_or_nan(arr):
    if isinstance(arr, list) and len(arr) == 0:
        return np.nan
    else:
        return np.mean(arr)


def model_info_name(model: entities.Model, package: entities.Package):
    if model is None:
        return "{}-no-model".format(package.name)
    else:
        return "{}-{}".format(package.name, model.name)


def measure_annotations(
        annotations_set_one: entities.AnnotationCollection,
        annotations_set_two: entities.AnnotationCollection,
        match_threshold=0.5,
        ignore_labels=False,
        ignore_attributes=False,
        compare_types=None):
    """
    Compares list (or collections) of annotations

    :param annotations_set_one: dl.AnnotationCollection entity with a list of annotations to compare
    :param annotations_set_two: dl.AnnotationCollection entity with a list of annotations to compare
    :param match_threshold: IoU threshold to count as a match
    :param ignore_labels: ignore label when comparing - measure only geometry
    :param ignore_attributes: ignore attribute score for final annotation score
    :param compare_types: list of type to compare. enum dl.AnnotationType

    Returns a dictionary of all the compare data
    """

    if compare_types is None:
        compare_types = [entities.AnnotationType.BOX,
                         entities.AnnotationType.CLASSIFICATION,
                         entities.AnnotationType.POLYGON,
                         entities.AnnotationType.POINT,
                         entities.AnnotationType.SEGMENTATION]
    final_results = dict()
    all_scores = list()

    # for local annotations - set random id if None
    for annotation in annotations_set_one:
        if annotation.id is None:
            annotation.id = str(uuid.uuid1())
    for annotation in annotations_set_two:
        if annotation.id is None:
            annotation.id = str(uuid.uuid1())

    # start comparing
    for compare_type in compare_types:
        matches = metrics.Matches()
        annotation_subset_one = entities.AnnotationCollection()
        annotation_subset_two = entities.AnnotationCollection()
        annotation_subset_one.annotations = [a for a in annotations_set_one if
                                             a.type == compare_type and not a.metadata.get('system', dict()).get(
                                                 'system', False)]
        annotation_subset_two.annotations = [a for a in annotations_set_two if
                                             a.type == compare_type and not a.metadata.get('system', dict()).get(
                                                 'system', False)]
        # create 2d dataframe with annotation id as names and set all to -1 -> not calculated
        if ignore_labels:
            matches = metrics.Matchers.general_match(matches=matches,
                                                     first_set=annotation_subset_one,
                                                     second_set=annotation_subset_two,
                                                     match_type=compare_type,
                                                     match_threshold=match_threshold,
                                                     ignore_labels=ignore_labels,
                                                     ignore_attributes=ignore_attributes)
        else:
            unique_labels = np.unique([a.label for a in annotation_subset_one] +
                                      [a.label for a in annotation_subset_two])
            for label in unique_labels:
                first_set = [a for a in annotation_subset_one if a.label == label]
                second_set = [a for a in annotation_subset_two if a.label == label]
                matches = metrics.Matchers.general_match(matches=matches,
                                                         first_set=first_set,
                                                         second_set=second_set,
                                                         match_type=compare_type,
                                                         match_threshold=match_threshold,
                                                         ignore_labels=ignore_labels,
                                                         ignore_attributes=ignore_attributes
                                                         )
        if len(matches) == 0:
            continue
        all_scores.extend(matches.to_df()['annotation_score'])
        final_results[compare_type] = metrics.Results(matches=matches,
                                                      annotation_type=compare_type)
    final_results['total_mean_score'] = mean_or_nan(all_scores)
    return final_results


def measure_item(ref_item: entities.Item, test_item: entities.Item,
                 ref_project: entities.Project = None, test_project: entities.Project = None,
                 ignore_labels=False,
                 ignore_attributes=False,
                 match_threshold=0.5,
                 pbar=None):
    """
    Compare annotations sets between two items

    :param ref_item:
    :param test_item:
    :param ref_project:
    :param test_project:
    :param ignore_labels:
    :param ignore_attributes:
    :param match_threshold:
    :param pbar:
    :return:
    """
    try:
        annotations_set_one = ref_item.annotations.list()
        annotations_set_two = test_item.annotations.list()
        final = measure_annotations(annotations_set_one=annotations_set_one,
                                    annotations_set_two=annotations_set_two,
                                    ignore_labels=ignore_labels,
                                    ignore_attributes=ignore_attributes,
                                    match_threshold=match_threshold)

        # get times
        try:
            ref_item_duration_s = metrics.item_annotation_duration(item=ref_item, project=ref_project)
            ref_item_duration = str(datetime.timedelta(seconds=int(np.round(ref_item_duration_s))))
        except Exception:
            ref_item_duration_s = -1
            ref_item_duration = ''

        try:
            test_item_duration_s = metrics.item_annotation_duration(item=test_item, project=test_project)
            test_item_duration = str(datetime.timedelta(seconds=int(np.round(test_item_duration_s))))
        except Exception:
            test_item_duration_s = -1
            test_item_duration = ''

        final.update({'ref_url': ref_item.platform_url,
                      'test_url': test_item.platform_url,
                      'filename': ref_item.filename,
                      'ref_item_duration[s]': ref_item_duration_s,
                      'test_item_duration[s]': test_item_duration_s,
                      'diff_duration[s]': test_item_duration_s - ref_item_duration_s,
                      # round to sec
                      'ref_item_duration': ref_item_duration,
                      'test_item_duration': test_item_duration,
                      })

        return True, final
    except Exception:
        fail_msg = 'failed measuring. ref_item: {!r}, test_item: {!r}'.format(ref_item.id, test_item.id)
        return False, '{}\n{}'.format(fail_msg, traceback.format_exc())
    finally:
        if pbar is not None:
            pbar.update()


def measure_items(ref_items, ref_project, ref_dataset, ref_name,
                  test_items, test_project, test_dataset, test_name,
                  dump_path=None):
    from multiprocessing.pool import ThreadPool
    ref_items_filepath_dict = {item.filename: item for page in ref_items for item in page}
    test_items_filepath_dict = {item.filename: item for page in test_items for item in page}
    pool = ThreadPool(processes=32)
    pbar = tqdm.tqdm(total=len(ref_items_filepath_dict), file=sys.stdout)
    jobs = dict()
    for filepath, ref_item in ref_items_filepath_dict.items():
        if filepath in test_items_filepath_dict:
            test_item = test_items_filepath_dict[filepath]
            jobs[ref_item.filename] = pool.apply_async(measure_item, kwds={'test_item': test_item,
                                                                           'ref_item': ref_item,
                                                                           'ref_project': ref_project,
                                                                           'test_project': test_project,
                                                                           'pbar': pbar})
    pool.close()
    pool.join()
    _ = [job.wait() for job in jobs.values()]
    raw_items_summary = dict()
    failed_items_errors = dict()
    for filename, job in jobs.items():
        success, result = job.get()
        if success:
            raw_items_summary[filename] = result
        else:
            failed_items_errors[filename] = result
    pool.terminate()
    pbar.close()

    df, raw_items_summary = create_summary(ref_name=ref_name, test_name=test_name, raw_items_summary=raw_items_summary)

    if len(failed_items_errors) != 0:
        logger.error(failed_items_errors)
    if dump_path is not None:
        save_to_file(dump_path=dump_path,
                     df=df,
                     ref_name=ref_name,
                     test_name=test_name)
    return df, raw_items_summary, failed_items_errors


def create_summary(ref_name, test_name, raw_items_summary):
    summary = list()
    ref_column_name = 'Ref-{!r}'.format(ref_name)
    test_column_name = 'Test-{!r}'.format(test_name)
    for filename, scores in raw_items_summary.items():
        line = {'filename': scores['filename'],
                ref_column_name: scores['ref_url'],
                test_column_name: scores['test_url'],
                'total_score': scores['total_mean_score'],
                'ref_duration[s]': scores['ref_item_duration[s]'],
                'test_duration[s]': scores['test_item_duration[s]'],
                'diff_duration[s]': scores['diff_duration[s]']}
        for tool_type in list(entities.AnnotationType):
            if tool_type in scores:
                res = scores[tool_type].summary()
                line['{}_annotation_score'.format(tool_type)] = res['mean_annotations_scores']
                line['{}_attributes_score'.format(tool_type)] = res['mean_attributes_scores']
                line['{}_ref_number'.format(tool_type)] = res['n_annotations_set_one']
                line['{}_test_number'.format(tool_type)] = res['n_annotations_set_two']
                line['{}_match_number'.format(tool_type)] = res['n_annotations_matched_total']
        summary.append(line)
    df = pd.DataFrame(summary)
    # Drop column only if all the values are None
    df = df.dropna(how='all', axis=1)
    ####

    return df, raw_items_summary


def save_to_file(df, dump_path, ref_name, test_name):
    # df = df.sort_values(by='box_score')
    ref_column_name = 'Ref-{!r}'.format(ref_name)
    test_column_name = 'Test-{!r}'.format(test_name)

    def make_clickable(val):
        return '<a href="{}">{}</a>'.format(val, 'item')

    s = df.style.format({ref_column_name: make_clickable,
                         test_column_name: make_clickable}).render()
    os.makedirs(dump_path, exist_ok=True)
    html_filepath = os.path.join(dump_path, '{}-vs-{}.html'.format(ref_name, test_name))
    csv_filepath = os.path.join(dump_path, '{}-vs-{}.csv'.format(ref_name, test_name))
    with open(html_filepath, 'w') as f:
        f.write(s)
    df.to_csv(csv_filepath)
