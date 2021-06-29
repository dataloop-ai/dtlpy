# Migrated from external repo at 2021-06-09 by shefi
import numpy as np
import pandas as pd
import warnings
import logging
import json

logger = logging.getLogger(__name__)

from .. import entities


def calculate_iou_box(pts1, pts2):
    """
    Measure the two list of points IoU
    :param pts1: ann.geo coordinates
    :param pts2: ann.geo coordinates
    :return: `float` how Intersection over Union of tho shapes
    """
    try:
        from shapely.geometry import Polygon
    except (ImportError, ModuleNotFoundError) as err:
        raise RuntimeError('dtlpy depends on external package. Please install ') from err
    poly_1 = Polygon([[pts1[0][0], pts1[0][1]],
                      [pts1[0][0], pts1[1][1]],
                      [pts1[1][0], pts1[1][1]],
                      [pts1[1][0], pts1[0][1]]])
    poly_2 = Polygon([[pts2[0][0], pts2[0][1]],
                      [pts2[0][0], pts2[1][1]],
                      [pts2[1][0], pts2[1][1]],
                      [pts2[1][0], pts2[0][1]]])
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


def calculate_iou_polygon(pts1, pts2):
    try:
        from shapely.geometry import Polygon
    except (ImportError, ModuleNotFoundError) as err:
        raise RuntimeError('dtlpy depends on external package. Please install ') from err
    poly_1 = Polygon(pts1)
    poly_2 = Polygon(pts2)
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


class Matching:
    def __init__(self, annotation_id):
        self.annotation_id = annotation_id
        self.annotation_score = 0
        self.attributes_score = 0
        self.match_annotation_id = None
        # Replace the old annotation score
        self.geometry_score = 0
        self.label_score = 0


def match_box(ref_annotations, test_annotations, match_thr=0.5, geometry_only=False):
    """
    :param geometry_only: `bool` if True ignores the label name
    Returns `dict` of annotation_id: `Matching`
    """
    # init all to zeros
    test_annotations_scores = {annotation.id: Matching(annotation.id) for annotation in test_annotations}
    ref_annotations_dict = {ref.id: ref for ref in ref_annotations}
    for t_annotation in test_annotations:
        ious_dict = {ref_id: -1 for ref_id in ref_annotations_dict.keys()}
        # Calculate the IoU (and annotation.id) for valid matches - same label
        for ref_ann_id, r_annotation in ref_annotations_dict.items():
            if not geometry_only:
                if t_annotation.label != r_annotation.label:
                    # TODO: split to geometry score and label score
                    continue
            ious_dict[ref_ann_id] = calculate_iou_box(pts1=r_annotation.geo, pts2=t_annotation.geo)
        if len(ious_dict) == 0:
            continue
        best_match_id = max(ious_dict, key=ious_dict.get)
        best_match_iou = ious_dict[best_match_id]
        if best_match_iou > match_thr:
            # add only if match - later we'll add the rest
            test_annotations_scores[t_annotation.id].match_annotation_id = best_match_id
            test_annotations_scores[t_annotation.id].annotation_score = best_match_iou
            test_annotations_scores[t_annotation.id].attributes_score = match_attributes(
                test_attrs=t_annotation.attributes,
                ref_attrs=ref_annotations_dict[best_match_id].attributes
            )
            test_annotations_scores[t_annotation.id].geometry_score = best_match_iou
            test_annotations_scores[t_annotation.id].label_score = match_labels(
                ref_label=ref_annotations_dict[best_match_id].label,
                test_label=t_annotation.label
            )

            # pop the matched annotation - so it wont be used any more
            _ = ref_annotations_dict.pop(best_match_id)
    return test_annotations_scores


def match_attributes(ref_attrs, test_attrs):
    """
    Returns IoU of the attributes. if No attributes returns 0
    0: no matching
    1: perfect attributes match
    """
    intersection = set(ref_attrs).intersection(set(test_attrs))
    union = set(ref_attrs).union(test_attrs)
    if len(union) == 0:
        return 1
    return len(intersection) / len(union)


def match_labels(ref_label, test_label):
    """Returns 1 in one of the labels in substring of the second"""
    return int(ref_label in test_label or test_label in ref_label)


def match_semantic(ref_annotations, test_annotations):
    annotations_scores = {annotation.id: Matching(annotation.id) for annotation in ref_annotations}
    test_annotations_inds = list(range(len(test_annotations)))
    for r_annotation in ref_annotations:
        ious = [-1] * len(test_annotations_inds)
        ious_ids = [-1] * len(test_annotations_inds)
        for i_ann, t_annotation in enumerate([test_annotations[ind] for ind in test_annotations_inds]):
            if t_annotation.label != r_annotation.label:
                continue
            mixed_fill = r_annotation.show(thickness=-1, annotation_format='instance', color=(1,)) + \
                         t_annotation.show(thickness=-1, annotation_format='instance', color=(1,))
            ious[i_ann] = np.sum(np.sum(mixed_fill == 2) / np.sum(mixed_fill > 0))
            ious_ids[i_ann] = t_annotation.id
        if ious and np.max(ious) > 0.5:
            # add only if match - later we'll add the rest
            annotations_scores[r_annotation.id].match_annotation_id = ious_ids[np.argmax(ious)]
            annotations_scores[r_annotation.id].annotation_score = np.max(ious)
            annotations_scores[r_annotation.id].attributes_score = match_attributes(ref_attrs=r_annotation.attributes,
                                                                                    test_attrs=test_annotations[
                                                                                        test_annotations_inds[np.argmax(
                                                                                            ious)]].attributes)
            test_annotations_inds.pop(np.argmax(ious))
    return annotations_scores


def match_polygon(ref_annotations, test_annotations):
    annotations_scores = {annotation.id: Matching(annotation.id) for annotation in ref_annotations}
    test_annotations_inds = list(range(len(test_annotations)))
    for r_annotation in ref_annotations:
        ious = [-1] * len(test_annotations_inds)
        ious_ids = [-1] * len(test_annotations_inds)

        for i_ann, t_annotation in enumerate([test_annotations[ind] for ind in test_annotations_inds]):
            if t_annotation.label != r_annotation.label:
                continue
            mixed_fill = r_annotation.show(thickness=-1, annotation_format='instance', color=(1,)) + \
                         t_annotation.show(thickness=-1, annotation_format='instance', color=(1,))
            ious[i_ann] = np.sum(np.sum(mixed_fill == 2) / np.sum(mixed_fill > 0))

        if ious:  # and np.max(ious) > 0.5:
            # add only if match - later we'll add the rest
            annotations_scores[r_annotation.id].match_annotation_id = ious_ids[np.argmax(ious)]
            annotations_scores[r_annotation.id].annotation_score = np.max(ious)
            annotations_scores[r_annotation.id].attributes_score = match_attributes(ref_attrs=r_annotation.attributes,
                                                                                    test_attrs=test_annotations[
                                                                                        test_annotations_inds[np.argmax(
                                                                                            ious)]].attributes)

            test_annotations_inds.pop(np.argmax(ious))
    return annotations_scores


def match_point(ref_annotations, test_annotations):
    warnings.warn("Under construction")
    return
    # TODO: Test ref / Test
    annotations_scores = {annotation.id: Matching(annotation.id) for annotation in test_annotations}

    # # Calculate using linear algebra
    # dist_mat = np.asarray([[np.linalg.norm(np.array((a.x, a.y)) - np.array((b.x,  b.y)))
    #                         for a in ref_annotations]
    #                        for b in test_annotations])
    # min_distances = np.min(dist_mat, axis=0)
    # annotations_scores = {annotation.id: min_dist for annotation, min_dist in zip(ref_annotations, min_distances)}

    for r_annotation in ref_annotations:
        if r_annotation.type != 'point':
            continue
        distances = list()
        for t_annotation in test_annotations:
            if t_annotation.type != 'point':
                continue
            if t_annotation.label != r_annotation.label:
                continue
            distances.append(np.sqrt(np.power(r_annotation.x - t_annotation.y, 2) +
                                     np.power(r_annotation.y - t_annotation.y, 2)))
        if distances:
            # annotations_scores[r_annotation] = np.min(distances)
            match_ind = np.argmin(distances)
            match_ann = ref_annotations[match_ind]

            annotations_scores[t_annotation.id].match_annotation_id = match_ann.id
            annotations_scores[t_annotation.id].annotation_score = np.min(distances)
            annotations_scores[t_annotation.id].attributes_score = match_attributes(
                test_attrs=t_annotation.attributes,
                ref_attrs=match_ann.attributes)

    return annotations_scores


def item_annotation_duration(item: entities.Item,
                             dataset: entities.Dataset = None,
                             project: entities.Project = None,
                             task: entities.Task = None,
                             assignment: entities.Assignment = None,
                             analytics_duration_df=None):
    query = {
        "match": {
            "action": ["annotation.created", "annotation.updated", 'annotation.deleted'],
            "itemId": item.id,
        },
        "size": 10000,
        'startTime': 0,
        "sort": {"by": 'time',
                 'order': 'asc'}
    }
    # add context for analytics
    if task is not None:
        query['match']['taskId'] = task.id
    if dataset is not None:
        query['match']['datasetId'] = dataset.id
    if assignment is not None:
        query['match']['assignmentId'] = assignment.id
    raw = project.analytics.get_samples(query=query, return_field='samples', return_raw=True)
    logger.debug("query for analytics: {}".format(json.dumps(query)))
    df = pd.DataFrame(raw)

    try:
        anns_duration_sec = df.loc[:, 'duration'].sum() / 1000
    except AttributeError as err:
        logger.warning("No annotations was found in analytics for item {}".format(item.id))
        anns_duration_sec = 0

    return anns_duration_sec
