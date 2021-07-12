import numpy as np
import pandas as pd
import os
import tqdm
import logging
import traceback
import datetime

from .. import entities
from . import BaseModelAdapter, metrics

logger = logging.getLogger(name=__name__)


# Utility functions to use in the model adapters
#   these wrapper function should ease to make sure all predictions are built with proper metadata structure


def create_collection():
    collection = entities.AnnotationCollection(item=None)
    return collection


def model_info_name(model: entities.Model, snapshot: entities.Snapshot):
    return "{}-{}".format(model.name, snapshot.name)


def add_box_prediction(left, top, right, bottom, label, score,
                       adapter: BaseModelAdapter = None,
                       model: entities.Model = None, snapshot: entities.Snapshot = None,
                       collection: entities.AnnotationCollection = None):
    if collection is None:
        collection = create_collection()

    if adapter is not None:
        model = adapter.model_entity
        snapshot = adapter.snapshot

    model_snap_name = model_info_name(model=model, snapshot=snapshot)
    collection.add(
        annotation_definition=entities.Box(
            left=float(left),
            top=float(top),
            right=float(right),
            bottom=float(bottom),
            label=str(label)
        ),
        model_info={
            'name': model_snap_name,
            'confidence': float(score),
            'model_id': model.id,
            'snapshot_id': snapshot.id
        }
    )
    return collection


def add_classification(label, score,
                       adapter: BaseModelAdapter = None,
                       model: entities.Model = None, snapshot: entities.Snapshot = None,
                       collection: entities.AnnotationCollection = None):
    if collection is None:
        collection = create_collection()

    if adapter is not None:
        model = adapter.model_entity
        snapshot = adapter.snapshot

    model_snap_name = model_info_name(model=model, snapshot=snapshot)
    collection.add(annotation_definition=entities.Classification(label=label),
                   model_info={
                       'name': model_snap_name,
                       'confidence': float(score),
                       'model_id': model.id,
                       'snapshot_id': snapshot.id
                   })
    return collection


def is_ann_pred(ann: entities.Annotation, model: entities.Model = None, snapshot: entities.Snapshot = None,
                verbose=False):
    is_pred = 'user' in ann.metadata and 'model_info' in ann.metadata['user']

    if is_pred and model is not None:
        is_pred = is_pred and model.id == ann.metadata['user']['model_info']['model_id']
        verbose and print("Annotation {!r} prediction with model mismatch".format(ann.id))

    if is_pred and snapshot is not None:
        is_pred = is_pred and snapshot.id == ann.metadata['user']['model_info']['snapshot_id']
        verbose and print("Annotation {!r} prediction with snapshot mismatch".format(ann.id))

    return is_pred


def measure_item_box_predictions(item: entities.Item, model: entities.Model = None, snapshot: entities.Snapshot = None):
    annotations = item.annotations.list(
        filters=entities.Filters(field='type', values='box', resource=entities.FiltersResource.ANNOTATION))
    actuals = [ann for ann in annotations if 'model_info' not in ann.metadata['user']]
    predictions = [ann for ann in annotations if is_ann_pred(ann, model=model, snapshot=snapshot)]

    r_boxes, t_boxes = actuals, predictions  # TODO: test if we need to change the order of ref /test

    box_scores = metrics.match_box(ref_annotations=r_boxes,
                                   test_annotations=t_boxes,
                                   geometry_only=True)
    # Create the symmetric IoU metric
    test_iou_scores = [match.annotation_score for match in box_scores.values() if match.annotation_score > 0]
    matched_box = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
    total_box = len(r_boxes) + len(t_boxes)
    extra_box = len(t_boxes) - matched_box
    missing_box = len(r_boxes) - matched_box
    assert total_box == extra_box + 2 * matched_box + missing_box
    # add missing to score
    test_iou_scores += [0 for i in range(missing_box)]
    test_iou_scores += [0 for i in range(extra_box)]

    boxes_report = {'box_ious': box_scores,
                    'box_annotations': r_boxes,
                    'box_mean_iou': np.mean(test_iou_scores),
                    'box_attributes_scores': np.mean([match.attributes_score for match in box_scores.values()]),
                    'box_ref_number': len(r_boxes),
                    'box_test_number': len(t_boxes),
                    'box_missing': missing_box,
                    'box_total': total_box,
                    'box_matched': matched_box,
                    'box_extra': extra_box,
                    }

    return boxes_report


def measure_annotations(
        test_annotations: entities.AnnotationCollection,
        ref_annotations: entities.AnnotationCollection,
        geometry_only=False):
    """
    Compares list (or collections) of annotations

    :param test_annotations: dl.AnnotationCollection entity with a list of annotations to test against ref_annotations (GT)
    :param ref_annotations: dl.AnnotationCollection entity with a list of annotations to perform as ground truth for the measure
    :param geometry_only: ignore label when comparing - measure only geometry
    Returns a dictionary of all the compare data
    """

    # Assign list per type of annotation
    t_boxes = [ann for ann in test_annotations if ann.type == 'box']
    t_polygons = [ann for ann in test_annotations if ann.type == 'segment']
    t_points = [ann for ann in test_annotations if ann.type == 'point']
    t_semantics = [ann for ann in test_annotations if ann.type == 'binary']
    un_supported = [ann for ann in test_annotations if ann.type not in (['box', 'segment', 'point', 'binary', 'class'])]
    if len(un_supported):
        logger.warning("test annotations have unsupported types {}:\n{}".
                       format([ann.type for ann in un_supported], un_supported))

    r_boxes = [ann for ann in ref_annotations if ann.type == 'box']
    r_polygons = [ann for ann in ref_annotations if ann.type == 'segment']
    r_points = [ann for ann in ref_annotations if ann.type == 'point']
    r_semantics = [ann for ann in ref_annotations if ann.type == 'binary']
    un_supported = [ann for ann in ref_annotations if ann.type not in (['box', 'segment', 'point', 'binary', 'class'])]
    if len(un_supported):
        logger.warning("test annotations have unsupported types {}:\n{}".
                       format([ann.type for ann in un_supported], un_supported))

    # match box
    box_scores = metrics.match_box(ref_annotations=r_boxes,
                                   test_annotations=t_boxes,
                                   geometry_only=geometry_only)
    # polygon
    polygon_scores = metrics.match_polygon(ref_annotations=r_polygons,
                                           test_annotations=t_polygons)
    # point
    point_scores = metrics.match_point(ref_annotations=r_points,
                                       test_annotations=t_points)
    # Semantic / Masks
    semantic_scores = metrics.match_semantic(ref_annotations=r_semantics,
                                             test_annotations=t_semantics)

    final = dict()
    # polygon
    if polygon_scores:
        test_iou_scores = [match.annotation_score for match in polygon_scores.values() if match.annotation_score > 0]
        matched_polygon = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
        total_polygon = len(r_polygons) + len(t_polygons)
        extra_polygon = len(t_polygons) - matched_polygon
        missing_polygon = len(r_polygons) - matched_polygon
        assert total_polygon == extra_polygon + 2 * matched_polygon + missing_polygon
        # add missing to score
        test_iou_scores += [0 for i in range(missing_polygon)]
        test_iou_scores += [0 for i in range(extra_polygon)]
        final.update(
            {'polygon_ious': polygon_scores,
             'polygon_annotations': r_polygons,
             'polygon_mean_iou': np.mean(test_iou_scores),
             'polygon_attributes_scores': np.mean([match.attributes_score for match in polygon_scores.values()]),
             'polygon_ref_number': len(r_polygons),
             'polygon_test_number': len(t_polygons),
             'polygon_missing': missing_polygon,
             'polygon_total': total_polygon,
             'polygon_matched': matched_polygon,
             'polygon_extra': extra_polygon,
             })
    # box
    if box_scores:
        test_iou_scores = [match.annotation_score for match in box_scores.values() if match.annotation_score > 0]
        matched_box = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
        total_box = len(r_boxes) + len(t_boxes)
        extra_box = len(t_boxes) - matched_box
        missing_box = len(r_boxes) - matched_box
        assert total_box == extra_box + 2 * matched_box + missing_box
        # add missing to score
        test_iou_scores += [0 for i in range(missing_box)]
        test_iou_scores += [0 for i in range(extra_box)]
        final.update(
            {'box_ious': box_scores,
             'box_annotations': r_boxes,
             'box_mean_iou': np.mean(test_iou_scores),
             'box_attributes_scores': np.mean([match.attributes_score for match in box_scores.values()]),
             'box_ref_number': len(r_boxes),
             'box_test_number': len(t_boxes),
             'box_missing': missing_box,
             'box_total': total_box,
             'box_matched': matched_box,
             'box_extra': extra_box,
             })
    # point
    if point_scores:
        test_iou_scores = [match.annotation_score for match in point_scores.values() if match.annotation_score > 0]
        matched_point = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
        total_point = len(r_points) + len(t_points)
        extra_point = len(t_points) - matched_point
        missing_point = len(r_points) - matched_point
        assert total_point == extra_point + 2 * matched_point + missing_point
        # add missing to score
        test_iou_scores += [0 for i in range(missing_point)]
        test_iou_scores += [0 for i in range(extra_point)]
        final.update(
            {'point_ious': point_scores,
             'point_annotations': r_points,
             'point_mean_iou': np.mean(test_iou_scores),
             'point_attributes_scores': np.mean([match.attributes_score for match in point_scores.values()]),
             'point_ref_number': len(r_points),
             'point_test_number': len(t_points),
             'point_missing': missing_point,
             'point_total': total_point,
             'point_matched': matched_point,
             'point_extra': extra_point,
             })
    # semantic
    if semantic_scores:
        test_iou_scores = [match.annotation_score for match in semantic_scores.values() if match.annotation_score > 0]
        matched_semantic = int(np.sum([1 for score in test_iou_scores if score > 0]))  # len(test_iou_scores)
        total_semantic = len(r_semantics) + len(t_semantics)
        extra_semantic = len(t_semantics) - matched_semantic
        missing_semantic = len(r_semantics) - matched_semantic
        assert total_semantic == extra_semantic + 2 * matched_semantic + missing_semantic
        # add missing to score
        test_iou_scores += [0 for i in range(missing_semantic)]
        test_iou_scores += [0 for i in range(extra_semantic)]
        final.update(
            {'semantic_ious': semantic_scores,
             'semantic_annotations': r_semantics,
             'semantic_mean_iou': np.mean(test_iou_scores),
             'semantic_attributes_scores': np.mean([match.attributes_score for match in semantic_scores.values()]),
             'semantic_ref_number': len(r_semantics),
             'semantic_test_number': len(t_semantics),
             'semantic_missing': missing_semantic,
             'semantic_total': total_semantic,
             'semantic_matched': matched_semantic,
             'semantic_extra': extra_semantic,
             })
    return final


def measure_item(ref_item: entities.Item,
                 test_item: entities.Item,
                 test_dataset: entities.Dataset = None,
                 ref_dataset: entities.Dataset = None,
                 ref_project: entities.Project = None,
                 test_project: entities.Project = None,
                 pbar=None):
    try:
        ref_annotations = ref_item.annotations.list()
        test_annotations = test_item.annotations.list()
        final = measure_annotations(ref_annotations=ref_annotations, test_annotations=test_annotations)

        # get times
        try:
            ref_item_duration_s = metrics.item_annotation_duration(item=ref_item, project=ref_project)
            test_item_duration_s = metrics.item_annotation_duration(item=test_item, project=test_project)
        except:
            logger.exception('failed getting analytics for item. setting duration to -1')
            ref_item_duration_s = -1
            test_item_duration_s = -1
        final.update({'ref_url': ref_item._client_api._get_resource_url(resource_type='item',
                                                                        project_id=ref_project.id,
                                                                        dataset_id=ref_dataset.id,
                                                                        item_id=ref_item.id),
                      'test_url': test_item._client_api._get_resource_url(resource_type='item',
                                                                          project_id=test_project.id,
                                                                          dataset_id=test_dataset.id,
                                                                          item_id=test_item.id),
                      'filename': ref_item.filename,
                      'ref_item_duration[s]': ref_item_duration_s,
                      'test_item_duration[s]': test_item_duration_s,
                      'diff_duration[s]': test_item_duration_s - ref_item_duration_s,
                      # round to sec
                      'ref_item_duration': str(datetime.timedelta(seconds=np.round(ref_item_duration_s))),
                      'test_item_duration': str(datetime.timedelta(seconds=np.round(test_item_duration_s))),
                      })

        return final

    except Exception:
        print(traceback.format_exc())
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
    pbar = tqdm.tqdm(total=len(ref_items_filepath_dict))
    jobs = dict()
    for filepath, ref_item in ref_items_filepath_dict.items():
        if filepath in test_items_filepath_dict:
            test_item = test_items_filepath_dict[filepath]
            jobs[ref_item.filename] = pool.apply_async(measure_item, kwds={'test_item': test_item,
                                                                           'ref_item': ref_item,
                                                                           'ref_dataset': ref_dataset,
                                                                           'test_dataset': test_dataset,
                                                                           'ref_project': ref_project,
                                                                           'test_project': test_project,
                                                                           'pbar': pbar})
    pool.close()
    pool.join()
    _ = [job.wait() for job in jobs.values()]
    items_summary = {filename: job.get() for filename, job in jobs.items() if job.get() is not None}
    pool.terminate()
    pbar.close()

    #
    summary = list()
    ref_column_name = 'Ref-{!r}'.format(ref_name)
    test_column_name = 'Test-{!r}'.format(test_name)
    for filename, scores in items_summary.items():
        has_box = 'box_test_number' in scores
        has_point = 'point_test_number' in scores
        has_polygon = 'polygon_test_number' in scores
        has_semantic = 'semantic_test_number' in scores
        line = {'filename': scores['filename'],
                ref_column_name: scores['ref_url'],
                test_column_name: scores['test_url'],
                'ref_duration[s]': scores['ref_item_duration[s]'],
                'test_duration[s]': scores['test_item_duration[s]'],
                'diff_duration[s]': scores['diff_duration[s]'],
                }
        if has_box:
            line['box_score'] = scores['box_mean_iou']
            line['box_attributes_score'] = np.mean(scores['box_attributes_scores'])
            line['box_ref_number'] = scores['box_ref_number']
            line['box_test_number'] = scores['box_test_number']
        if has_point:
            line['point_score'] = scores['point_mean_iou']
            line['point_attributes_score'] = np.mean(scores['point_attributes_scores'])
            line['point_ref_number'] = scores['point_ref_number']
            line['point_test_number'] = scores['point_test_number']
        if has_polygon:
            line['polygon_score'] = scores['polygon_mean_iou']
            line['polygon_attributes_score'] = np.mean(scores['polygon_attributes_scores'])
            line['polygon_ref_number'] = scores['polygon_ref_number']
            line['polygon_test_number'] = scores['polygon_test_number']
        if has_semantic:
            line['semantic_score'] = scores['semantic_mean_iou']
            line['semantic_attributes_score'] = np.mean(scores['semantic_attributes_scores'])
            line['semantic_ref_number'] = scores['semantic_ref_number']
            line['semantic_test_number'] = scores['semantic_test_number']
        summary.append(line)
    # columns = ['filename', ref_column_name, test_column_name, 'ref_duration', 'test_duration',
    #            'semantic_score', 'semantic_ref_number', 'semantic_test_number',
    #            'polygon_score', 'polygon_ref_number', 'polygon_test_number',
    #            'box_score', 'box_attributes_score', 'box_ref_number', 'box_test_number',
    #            'point_score', 'point_ref_number', 'point_test_number']
    df = pd.DataFrame(summary)  # ,                      columns=columns)
    # Drop column only if all the values are None
    df = df.dropna(how='all', axis=1)
    ####
    if dump_path is not None:
        save_to_file(dump_path=dump_path,
                     df=df,
                     ref_name=ref_name,
                     test_name=test_name)
    return df


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
