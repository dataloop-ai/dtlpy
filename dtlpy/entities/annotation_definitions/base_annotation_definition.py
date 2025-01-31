import logging
import numpy as np
import warnings

logger = logging.getLogger(name='dtlpy')


class BaseAnnotationDefinition:
    def __init__(self, description=None, attributes=None):
        self.description = description
        self._top = 0
        self._left = 0
        self._bottom = 0
        self._right = 0
        self._annotation = None

        if isinstance(attributes, list) and len(attributes) > 0:
            warnings.warn("List attributes are deprecated and will be removed in version 1.109. Use Attribute 2.0 (Dictionary) instead."
                "For more details, refer to the documentation: "
                "https://developers.dataloop.ai/tutorials/data_management/upload_and_manage_annotations/chapter/#set-attributes-on-annotations",
                DeprecationWarning,
            )
        self._attributes = attributes

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, v):
        if isinstance(v, list):
            warnings.warn("List attributes are deprecated and will be removed in version 1.109. Use Attribute 2.0 (Dictionary) instead. "
                "For more details, refer to the documentation: "
                "https://developers.dataloop.ai/tutorials/data_management/upload_and_manage_annotations/chapter/#set-attributes-on-annotations",
                DeprecationWarning,
            )
        self._attributes = v
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
                           org=tuple([int(np.round(left)), int(np.round(top))]),
                           color=(255, 0, 0),
                           fontFace=cv2.FONT_HERSHEY_DUPLEX,
                           fontScale=1,
                           thickness=2)

    @property
    def logger(self):
        return logger
