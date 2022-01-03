import numpy as np
# import open3d as o3d
from . import BaseAnnotationDefinition
# from scipy.spatial.transform import Rotation as R
import logging

logger = logging.getLogger(name='dtlpy')


class Cube3d(BaseAnnotationDefinition):
    """
        Cube annotation object
    """
    type = "cube_3d"

    def __init__(self, label, position, scale, rotation,
                 attributes=None, description=None):
        """
        :param label:
        :param position: the XYZ position of the ‘center’ of the annotation.
        :param scale: the scale of the object by each axis (XYZ).
        :param rotation: an euler representation of the object rotation on each axis (with rotation order ‘XYZ’). (rotation in radians)
        :param attributes:
        :param description:
        """
        super().__init__(description=description, attributes=attributes)

        self.position = position
        self.scale = scale
        self.rotation = rotation
        self.label = label

    def _translate(self, points, translate_x, translate_y, translate_z):
        translation_matrix = np.array([[1, 0, 0, 0],
                                       [0, 1, 0, 0],
                                       [0, 0, 1, 0],
                                       [translate_x, translate_y, translate_z, 1]])

        matrix = [(list(i) + [1]) for i in points]
        pts2 = np.dot(matrix, translation_matrix)
        return [pt[:3] for pt in pts2]

    # def make_points(self):
    #     simple = [
    #         [self.scale[0] / 2, self.scale[1] / 2, self.scale[2] / 2],
    #         [-self.scale[0] / 2, self.scale[1] / 2, self.scale[2] / 2],
    #         [self.scale[0] / 2, -self.scale[1] / 2, self.scale[2] / 2],
    #         [self.scale[0] / 2, self.scale[1] / 2, -self.scale[2] / 2],
    #         [-self.scale[0] / 2, -self.scale[1] / 2, self.scale[2] / 2],
    #         [self.scale[0] / 2, -self.scale[1] / 2, -self.scale[2] / 2],
    #         [-self.scale[0] / 2, self.scale[1] / 2, -self.scale[2] / 2],
    #         [-self.scale[0] / 2, -self.scale[1] / 2, -self.scale[2] / 2],
    #     ]
    #
    #     # matrix = R.from_euler('xyz', self.rotation, degrees=False)
    #
    #     vecs = [np.array(p) for p in simple]
    #     rotated = matrix.apply(vecs)
    #     translation = np.array(self.position)
    #     dX = translation[0]
    #     dY = translation[1]
    #     dZ = translation[2]
    #     points = self._translate(rotated, dX, dY, dZ)
    #     return points

    @property
    def geo(self):
        return np.asarray([
            list(self.position),
            list(self.scale),
            list(self.rotation)
        ])

    def show(self, image, thickness, with_text, height, width, annotation_format, color, alpha=1):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: options: list(dl.ViewAnnotationOptions)
        :param color: color
        :param alpha: opacity value [0 1], default 1
        :return: ndarray
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            self.logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise
        points = self.make_points()
        front_bl = points[0]
        front_br = points[1]
        front_tr = points[2]
        front_tl = points[3]
        back_bl = points[4]
        back_br = points[5]
        back_tr = points[6]
        back_tl = points[7]
        logger.warning('the show for 3d_cube is not supported.')
        return image

        # image = np.zeros((100, 100, 100), dtype=np.uint8)
        # pcd = o3d.io.read_point_cloud(r"C:\Users\97250\PycharmProjects\tt\qw\3D\D34049418_0000635.las.pcd")
        # # o3d.visualization.draw_geometries([pcd])
        # # points = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1],
        # #           [0, 1, 1], [1, 1, 1]]
        # lines = [[0, 1], [0, 2], [1, 3], [2, 3], [4, 5], [4, 6], [5, 7], [6, 7],
        #          [0, 4], [1, 5], [2, 6], [3, 7]]
        # colors = [[1, 0, 0] for i in range(len(lines))]
        # points = [back_bl, back_br, back_tl, back_tr, front_bl, front_br, front_tl, front_tr]
        # line_set = o3d.geometry.LineSet()
        # line_set.points = o3d.utility.Vector3dVector(points)
        # line_set.lines = o3d.utility.Vector2iVector(lines)
        # line_set.colors = o3d.utility.Vector3dVector(colors)
        # o3d.visualization.draw_geometries([line_set])
        # return image

    def to_coordinates(self, color=None):
        keys = ["position", "scale", "rotation"]
        coordinates = {keys[idx]: {"x": float(x), "y": float(y), "z": float(z)}
                       for idx, [x, y, z] in enumerate(self.geo)}
        return coordinates

    @staticmethod
    def from_coordinates(coordinates):
        geo = list()
        for key, pt in coordinates.items():
            geo.append([pt["x"], pt["y"], pt["z"]])
        return np.asarray(geo)

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            key = "coordinates"
        elif "data" in _json:
            key = "data"
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        return cls(
            position=list(_json[key]['position'].values()),
            scale=list(_json[key]['scale'].values()),
            rotation=list(_json[key]['rotation'].values()),
            label=_json["label"],
            attributes=_json.get("attributes", None)
        )
