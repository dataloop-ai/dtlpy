import behave
import os
from PIL import Image
import cv2


@behave.when(u'I get items mask in "{download_path}"')
def step_impl(context, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    item = context.dataset.items.get(item_id=context.item.id)
    img_shape = (item.metadata["system"]["height"], item.metadata["system"]["width"])
    context.mask = context.item.annotations.to_mask(img_shape=img_shape, thickness=1)
    img = Image.fromarray(context.mask)
    img.save(download_path)


@behave.then(u'Items mask in "{download_path}" match Items mask in "{origin_path}"')
def step_impl(context, download_path, origin_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    origin_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], origin_path)

    original = cv2.imread(download_path)
    downloaded = cv2.imread(origin_path)
    if original.shape == downloaded.shape:
        difference = cv2.subtract(original, downloaded)
        b, g, r = cv2.split(difference)
        if cv2.countNonZero(b) < 3 and cv2.countNonZero(g) < 3 and cv2.countNonZero(r) < 3:
            assert True
        else:
            assert False
    else:
        assert False


# @behave.then(u"Items mask match annotations")
# def step_impl(context):
#     path = 'assets/0000000162.png'
#     test_dir = os.path.abspath(os.path.join(os.path.realpath(''), os.pardir))
#     path = os.path.join(test_dir, path)

#     mask = context.mask
#     context.labels = context.dataset.get_labels()
#     colors = list()
#     ann = ImageAnnotation()
#     for clss in context.labels:
#         color = clss["value"]["color"]
#         color = tuple(int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
#         color = (color[0], color[1], color[2], 255)
#         label = clss["value"]["tag"]
#         ann_type = "box"
#         new_mask = numpy.bitwise_and(mask[:, :, 0] == color[0], mask[:, :, 1] == color[1])
#         new_mask = numpy.bitwise_and(new_mask, mask[:, :, 2] == color[2])
#         new_mask = numpy.bitwise_and(new_mask, mask[:, :, 3] > 127)
#         ann.add_annotation(pts=new_mask, label=label, annotation_type=ann_type, color=color)
#     context.item_match = context.dataset.items.upload(filepath=path, uploaded_filename='some_name')
#     context.item_match.annotations.upload(ann.to_platform())
#     print()

@behave.then(u"Mask has been downloaded properly")
def step_impl(context):
    raise NotImplementedError(u"STEP: Then Mask has been downloaded properly")
