import behave
import os
import numpy as np


@behave.when(u'I draw items annotations with param "{annotation_format}" to image in "{im_path}"')
def step_impl(context, annotation_format, im_path):
    im_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], im_path)
    context.img_arr = np.load(im_path + '.npy')

    context.img_arr = context.img_arr.copy()
    context.item = context.item.update()
    context.mask = context.item.annotations.show(height=768, width=1536, annotation_format=annotation_format,
                                                 image=context.img_arr)
