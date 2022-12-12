import behave
import os


@behave.given(u'I upload annotation in the path "{annotation_path}" to the item')
def step_impl(context, annotation_path):
    context.annotation_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotation_path)
    context.annotation = context.item.annotations.upload(annotations=context.annotation_path)[0]
