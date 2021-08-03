import behave
import os
import numpy as np


@behave.when(u'I show items annotations with param "{annotation_format}"')
def step_impl(context, annotation_format):
    context.item = context.item.update()
    annotation_collection = context.item.annotations.list()

    annotation_collection.annotations = sorted(annotation_collection.annotations, key=lambda x: x.top)
    context.mask = annotation_collection.show(height=768,
                                              width=1536,
                                              thickness=1,
                                              with_text=False,
                                              annotation_format=annotation_format)


@behave.then(u'I receive annotations mask and it is equal to mask in "{should_be_path}"')
def step_impl(context, should_be_path):
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)
    if not np.array_equal(context.mask, np.load(should_be_path)):
        np.save(should_be_path.replace('.npy', '_wrong.npy'), context.mask)
        assert False


@behave.when(u'Every annotation has an object id')
def step_impl(context):
    context.annotaitons = context.item.annotations.list()
    types = ['ellipse', 'segment', 'box', 'point', 'polyline']
    for ann in context.annotaitons:
        if ann.type == 'polyline':
            ann.object_id = 2
        else:
            ann.object_id = types.index(ann.type) + 1
    context.annotaitons = context.annotaitons.update()
