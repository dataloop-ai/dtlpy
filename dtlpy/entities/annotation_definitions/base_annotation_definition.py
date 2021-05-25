import logging
import numpy as np

logger = logging.getLogger(name=__name__)


class BaseAnnotationDefinition:
    def __init__(self, description=None):
        self.description = description

    @staticmethod
    def add_text_to_image(image, annotation):
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
