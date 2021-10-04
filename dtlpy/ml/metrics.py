# Migrated from external repo at 2021-06-09 by shefi
import numpy as np
import pandas as pd
import logging
import json

from .. import entities

logger = logging.getLogger(__name__)


class Matching:
    def __init__(self, annotation_id):
        self.annotation_id = annotation_id
        self.annotation_score = 0
        self.attributes_score = 0
        self.match_annotation_id = None
        # Replace the old annotation score
        self.geometry_score = 0
        self.label_score = 0

    def __repr__(self):
        return 'annotation: {:.2f}, attributes: {:.2f}, geomtry: {:.2f}, label: {:.2f}'.format(
            self.annotation_score, self.attributes_score, self.geometry_score, self.label_score)


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
    if len(pts1) == 2:
        # regular box annotation (2 pts)
        pt1_left_top = [pts1[0][0], pts1[0][1]]
        pt1_right_top = [pts1[0][0], pts1[1][1]]
        pt1_right_bottom = [pts1[1][0], pts1[1][1]]
        pt1_left_bottom = [pts1[1][0], pts1[0][1]]
    else:
        # rotated box annotation (4 pts)
        pt1_left_top = pts1[0]
        pt1_right_top = pts1[3]
        pt1_left_bottom = pts1[1]
        pt1_right_bottom = pts1[2]

    poly_1 = Polygon([pt1_left_top,
                      pt1_right_top,
                      pt1_right_bottom,
                      pt1_left_bottom])

    if len(pts2) == 2:
        # regular box annotation (2 pts)
        pt2_left_top = [pts2[0][0], pts2[0][1]]
        pt2_right_top = [pts2[0][0], pts2[1][1]]
        pt2_right_bottom = [pts2[1][0], pts2[1][1]]
        pt2_left_bottom = [pts2[1][0], pts2[0][1]]
    else:
        # rotated box annotation (4 pts)
        pt2_left_top = pts2[0]
        pt2_right_top = pts2[3]
        pt2_left_bottom = pts2[1]
        pt2_right_bottom = pts2[2]

    poly_2 = Polygon([pt2_left_top,
                      pt2_right_top,
                      pt2_right_bottom,
                      pt2_left_bottom])
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


def calculate_iou_polygon(pts1, pts2):
    try:
        # from shapely.geometry import Polygon
        import cv2
    except (ImportError, ModuleNotFoundError) as err:
        raise RuntimeError('dtlpy depends on external package. Please install ') from err
    # # using shapley
    # poly_1 = Polygon(pts1)
    # poly_2 = Polygon(pts2)
    # iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area

    # # using opencv
    width = int(np.ceil(np.max(np.concatenate((pts1[:, 0], pts2[:, 0]))))) + 10
    height = int(np.ceil(np.max(np.concatenate((pts1[:, 1], pts2[:, 1]))))) + 10
    mask1 = np.zeros((height, width))
    mask2 = np.zeros((height, width))
    mask1 = cv2.drawContours(
        image=mask1,
        contours=[pts1.round().astype(int)],
        contourIdx=-1,
        color=1,
        thickness=-1,
    )
    mask2 = cv2.drawContours(
        image=mask2,
        contours=[pts2.round().astype(int)],
        contourIdx=-1,
        color=1,
        thickness=-1,
    )
    iou = np.sum((mask1 + mask2) == 2) / np.sum((mask1 + mask2) > 0)
    if np.sum((mask1 + mask2) > 2):
        assert False
    return iou


def match_class(ref_annotations, test_annotations):
    """
    Return matching scores between two sets of annotations
    :param ref_annotations: list of reference annotation (GT)
    :param test_annotations: list of test annotations
    Returns `dict` of annotation_id: `Matching`
    """
    # init all to zeros
    test_annotations_scores = {annotation.id: Matching(annotation.id) for annotation in test_annotations}
    ref_annotations_dict = {ref.id: ref for ref in ref_annotations}
    for t_annotation in test_annotations:
        # Calculate the IoU (and annotation.id) for valid matches - same label
        for ref_ann_id, r_annotation in ref_annotations_dict.items():
            if r_annotation.label == t_annotation.label:
                # add only if match - later we'll add the rest
                test_annotations_scores[t_annotation.id].match_annotation_id = r_annotation.id
                test_annotations_scores[t_annotation.id].annotation_score = 1
                test_annotations_scores[t_annotation.id].geometry_score = 1
                test_annotations_scores[t_annotation.id].attributes_score = match_attributes(
                    ref_attrs=r_annotation.attributes,
                    test_attrs=t_annotation.attributes
                )
                test_annotations_scores[t_annotation.id].label_score = match_labels(
                    ref_label=r_annotation.label,
                    test_label=t_annotation.label
                )
                # pop the matched annotation - so it wont be used any more
                _ = ref_annotations_dict.pop(r_annotation.id)
                break
    return test_annotations_scores


def match_box(ref_annotations, test_annotations, match_thr=0.5, geometry_only=False):
    """
    Return matching scores between two sets of annotations
    :param ref_annotations: list of reference annotation (GT)
    :param test_annotations: list of test annotations
    :param match_thr: float - matching annotation iou threshold
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
            try:
                ious_dict[ref_ann_id] = calculate_iou_box(pts1=r_annotation.geo, pts2=t_annotation.geo)
            except:
                logger.debug('failed calculating. ref annotation: {!r}, test annotation: {!r}'.format(
                    r_annotation.id, t_annotation.id
                ))
                raise
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


def match_semantic(ref_annotations, test_annotations, match_thr=0.5, geometry_only=False):
    """
    Return matching scores between two sets of annotations

    :param ref_annotations: list of reference annotation (GT)
    :param test_annotations: list of test annotations
    :param match_thr: float - matching annotation iou threshold
    :param geometry_only: `bool` if True ignores the label name

    Returns `dict` of annotation_id: `Matching`
    """
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
            joint_mask = r_annotation.show(thickness=-1, annotation_format='instance', color=(1,)) + \
                         t_annotation.show(thickness=-1, annotation_format='instance', color=(1,))
            mask_iou = np.sum(np.sum(joint_mask == 2) / np.sum(joint_mask > 0))
            ious_dict[ref_ann_id] = mask_iou
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


def match_polygon(ref_annotations, test_annotations, match_thr=0.5, geometry_only=False):
    """
        Return matching scores between two sets of annotations
        :param ref_annotations: list of reference annotation (GT)
        :param test_annotations: list of test annotations
        :param match_thr: float - matching annotation iou threshold
        :param geometry_only: `bool` if True ignores the label name
        Returns `dict` of annotation_id: `Matching`
    """
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
            try:
                ious_dict[ref_ann_id] = calculate_iou_polygon(pts1=r_annotation.geo, pts2=t_annotation.geo)
            except:
                logger.debug('failed calculating. ref annotation: {!r}, test annotation: {!r}'.format(
                    r_annotation.id, t_annotation.id
                ))
                raise
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


def match_point(ref_annotations, test_annotations, match_thr=100, geometry_only=False):
    """
    Return matching scores between two sets of annotations
    :param ref_annotations: list of reference annotation (GT)
    :param test_annotations: list of test annotations
    :param match_thr: float - matching annotation iou threshold
    :param geometry_only: `bool` if True ignores the label name
    Returns `dict` of annotation_id: `Matching`

    """
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
            point_dist = np.linalg.norm(np.array((r_annotation.x, r_annotation.y)) -
                                        np.array((t_annotation.x, t_annotation.y)))
            if point_dist > match_thr:
                continue
            # to create a score between [0, 1] - 1 is the exact match
            noramlized_dist = np.abs(point_dist - match_thr) / match_thr
            ious_dict[ref_ann_id] = noramlized_dist
        if len(ious_dict) == 0:
            continue
        best_match_id = max(ious_dict, key=ious_dict.get)
        best_match_iou = ious_dict[best_match_id]
        if best_match_iou < match_thr:
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

    if 'duration' in df.columns:
        anns_duration_sec = df.loc[:, 'duration'].sum() / 1000
    else:
        anns_duration_sec = 0

    return anns_duration_sec
