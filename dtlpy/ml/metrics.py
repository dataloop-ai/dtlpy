import numpy as np
import pandas as pd
import logging
import json

from .. import entities

logger = logging.getLogger('dtlpy')


class Results:
    def __init__(self, matches, annotation_type):
        self.matches = matches
        self.annotation_type = annotation_type

    def to_df(self):
        return self.matches.to_df()

    def summary(self):
        df = self.matches.to_df()
        total_set_one = len(df['first_id'].dropna())
        total_set_two = len(df['second_id'].dropna())
        # each set unmatched is the number of Nones from the other set
        unmatched_set_one = df.shape[0] - total_set_two
        unmatched_set_two = df.shape[0] - total_set_one
        matched_set_one = total_set_one - unmatched_set_one
        matched_set_two = total_set_two - unmatched_set_two
        # sanity
        assert matched_set_one == matched_set_two, 'matched numbers are not the same'
        assert df['annotation_score'].shape[0] == (unmatched_set_one + unmatched_set_two + matched_set_one), \
            'mis-match number if scores and annotations'
        return {
            'annotation_type': self.annotation_type,
            'mean_annotations_scores': df['annotation_score'].mean(),
            'mean_attributes_scores': df['attribute_score'].mean(),
            'mean_labels_scores': df['label_score'].mean(),
            'n_annotations_set_one': total_set_one,
            'n_annotations_set_two': total_set_two,
            'n_annotations_total': total_set_one + total_set_two,
            'n_annotations_unmatched_set_one': unmatched_set_one,
            'n_annotations_unmatched_set_two': unmatched_set_two,
            'n_annotations_unmatched_total': unmatched_set_one + unmatched_set_two,
            'n_annotations_matched_total': matched_set_one,
        }


class Match:
    def __init__(self, first_annotation_id, second_annotation_id,
                 # defaults
                 annotation_score=0, attributes_score=0, geometry_score=0, label_score=0):
        self.first_annotation_id = first_annotation_id
        self.second_annotation_id = second_annotation_id
        self.annotation_score = annotation_score
        self.attributes_score = attributes_score
        # Replace the old annotation score
        self.geometry_score = geometry_score
        self.label_score = label_score

    def __repr__(self):
        return 'annotation: {:.2f}, attributes: {:.2f}, geomtry: {:.2f}, label: {:.2f}'.format(
            self.annotation_score, self.attributes_score, self.geometry_score, self.label_score)


class Matches:
    def __init__(self):
        self.matches = list()

    def __len__(self):
        return len(self.matches)

    def __repr__(self):
        return self.to_df().to_string()

    def to_df(self):
        results = list()
        for match in self.matches:
            results.append({
                'first_id': match.first_annotation_id,
                'second_id': match.second_annotation_id,
                'annotation_score': match.annotation_score,
                'attribute_score': match.attributes_score,
                'geometry_score': match.geometry_score,
                'label_score': match.label_score,
            })
        df = pd.DataFrame(results)
        return df

    def add(self, match: Match):
        self.matches.append(match)

    def validate(self):
        first = list()
        second = list()
        for match in self.matches:
            if match.first_annotation_id in first:
                raise ValueError('duplication for annotation id {!r} in FIRST set'.format(match.first_annotation_id))
            if match.first_annotation_id is not None:
                first.append(match.first_annotation_id)
            if match.second_annotation_id in second:
                raise ValueError('duplication for annotation id {!r} in SECOND set'.format(match.second_annotation_id))
            if match.second_annotation_id is not None:
                second.append(match.second_annotation_id)
        return True

    def find(self, annotation_id, loc='first'):
        for match in self.matches:
            if loc == 'first':
                if match.first_annotation_id == annotation_id:
                    return match
            elif loc == 'second':
                if match.second_annotation_id == annotation_id:
                    return match
        raise ValueError('could not find annotation id {!r} in {}'.format(annotation_id, loc))


######################
# Matching functions #
######################
class Matchers:

    @staticmethod
    def calculate_iou_box(pts1, pts2, config):
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

    @staticmethod
    def calculate_iou_classification(pts1, pts2, config):
        """
        Measure the two list of points IoU
        :param pts1: ann.geo coordinates
        :param pts2: ann.geo coordinates
        :return: `float` how Intersection over Union of tho shapes
        """
        return 1

    @staticmethod
    def calculate_iou_polygon(pts1, pts2, config):
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

    @staticmethod
    def calculate_iou_semantic(mask1, mask2, config):
        joint_mask = mask1 + mask2
        return np.sum(np.sum(joint_mask == 2) / np.sum(joint_mask > 0))

    @staticmethod
    def calculate_iou_point(pt1, pt2, config):
        """
        pt is [x,y]
        normalizing  to score  between [0, 1] -> 1 is the exact match
        if same point score is 1
        at about 20 pix distance score is about 0.5, 100 goes to 0
        :param pt1:
        :param pt2:
        :return:
        """
        """
        x = np.arange(int(diag))
        y = np.exp(-1 / diag * 20 * x)
        plt.figure()
        plt.plot(x, y)
        """
        height = config.get('height', 500)
        width = config.get('width', 500)
        diag = np.sqrt(height ** 2 + width**2)
        # 20% of the image diagonal tolerance (empirically). need to
        return np.exp(-1 / diag * 20 * np.linalg.norm(np.asarray(pt1) - np.asarray(pt2)))

    @staticmethod
    def match_attributes(attributes1, attributes2):
        """
        Returns IoU of the attributes. if both are empty - its a prefect match (returns 1)
        0: no matching
        1: perfect attributes match
        """
        if type(attributes1) is not type(attributes2):
            logger.warning('attributes are not same type: {}, {}'.format(type(attributes1), type(attributes2)))
            return 0

        if attributes1 is None and attributes2 is None:
            return 1

        if isinstance(attributes1, dict) and isinstance(attributes2, dict):
            # convert to list
            attributes1 = ['{}-{}'.format(key, val) for key, val in attributes1.items()]
            attributes2 = ['{}-{}'.format(key, val) for key, val in attributes2.items()]

        intersection = set(attributes1).intersection(set(attributes2))
        union = set(attributes1).union(attributes2)
        if len(union) == 0:
            # if there is no union - there are no attributes at all
            return 1
        return len(intersection) / len(union)

    @staticmethod
    def match_labels(label1, label2):
        """
        Returns 1 in one of the labels in substring of the second
        """
        return int(label1 in label2 or label2 in label1)

    @staticmethod
    def general_match(matches, first_set, second_set, match_type, match_threshold):
        annotation_type_to_func = {
            entities.AnnotationType.BOX: Matchers.calculate_iou_box,
            entities.AnnotationType.CLASSIFICATION: Matchers.calculate_iou_classification,
            entities.AnnotationType.SEGMENTATION: Matchers.calculate_iou_semantic,
            entities.AnnotationType.POLYGON: Matchers.calculate_iou_polygon,
            entities.AnnotationType.POINT: Matchers.calculate_iou_point,
        }
        df = pd.DataFrame(data=-1 * np.ones((len(second_set), len(first_set))),
                          columns=[a.id for a in first_set],
                          index=[a.id for a in second_set])
        for annotation_one in first_set:
            for annotation_two in second_set:
                if match_type not in annotation_type_to_func:
                    raise ValueError('unsupported type: {}'.format(match_type))
                if df[annotation_one.id][annotation_two.id] == -1:
                    try:
                        config = {'height': annotation_one._item.height if annotation_one._item is not None else 500,
                                  'width': annotation_one._item.width if annotation_one._item is not None else 500}
                        df[annotation_one.id][annotation_two.id] = annotation_type_to_func[match_type](
                            annotation_one.geo,
                            annotation_two.geo,
                            config)
                    except np.ZeroDivisionError:
                        logger.warning(
                            'Found annotations with area=0!: annotations ids: {!r}, {!r}'.format(annotation_one.id,
                                                                                                 annotation_two.id))
                        df[annotation_one.id][annotation_two.id] = 0

        while True:
            # take max IoU score, list the match and remove annotations' ids from columns and rows
            # keep doing that until no more matches or lower than match threshold
            max_cell = df.max().max()
            if max_cell < match_threshold or np.isnan(max_cell):
                break
            loc = df.where(df == max_cell).dropna(how='all').dropna(axis=1)
            first_annotation_id = loc.columns[0]
            second_annotation_id = loc.index[0]
            first_annotation = [a for a in first_set if a.id == first_annotation_id][0]
            second_annotation = [a for a in second_set if a.id == second_annotation_id][0]
            val = loc.values[0][0]
            labels_score = Matchers.match_labels(label1=first_annotation.label,
                                                 label2=second_annotation.label)
            attribute_score = Matchers.match_attributes(attributes1=first_annotation.attributes,
                                                        attributes2=second_annotation.attributes)
            matches.add(Match(first_annotation_id=first_annotation_id,
                              second_annotation_id=second_annotation_id,
                              annotation_score=val,
                              label_score=labels_score,
                              attributes_score=attribute_score))
            df.drop(index=second_annotation_id, inplace=True)
            df.drop(columns=first_annotation_id, inplace=True)
        # add un-matched
        for second_id in df.index:
            matches.add(match=Match(first_annotation_id=None,
                                    second_annotation_id=second_id))
        for first_id in df.columns:
            matches.add(match=Match(first_annotation_id=first_id,
                                    second_annotation_id=None))
        return matches


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
