import logging
import numpy as np

logger = logging.getLogger(name=__name__)


class BaseAnnotationDefinition:
    def __init__(self, description=None):
        self.description = description
        self._top = 0
        self._left = 0
        self._bottom = 0
        self._right = 0

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, v):
        self._top = v

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, v):
        self._left = v

    @property
    def bottom(self):
        return self._bottom

    @bottom.setter
    def bottom(self, v):
        self._bottom = v

    @property
    def right(self):
        return self._right

    @right.setter
    def right(self, v):
        self._right = v

    @property
    def height(self):
        return np.round(self.bottom - self.top)

    @property
    def width(self):
        return np.round(self.right - self.left)

    @staticmethod
    def add_text_to_image(image, annotation):
        """
        :param image:
        :param annotation:
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        text = '{label}-{attributes}'.format(label=annotation.label, attributes=','.join(annotation.attributes))
        top = annotation.top
        left = annotation.left
        if top == 0:
            top = image.shape[0] / 10
        if left == 0:
            left = image.shape[1] / 10
        return cv2.putText(img=image,
                           text=text,
                           org=tuple([int(np.round(top)), int(np.round(left))]),
                           color=(255, 0, 0),
                           fontFace=cv2.FONT_HERSHEY_DUPLEX,
                           fontScale=1,
                           thickness=2)

    @property
    def logger(self):
        return logger
