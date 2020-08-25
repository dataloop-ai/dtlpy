from behave import given, then, when
from PIL import Image
import numpy
import os
import dtlpy as dl


@given(u'I convert to Numpy.NdArray an item with the name "{item_path}" and add it to context.array')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    image = Image.open(item_path)
    context.array = numpy.array(image)


@given(u'I save item_metadata context.item_metadata')
def step_impl(context):
    context.item_metadata = {'City': 'NY', 'Country': 'USA'}


@when(u'I Upload an Numpy.NdArray (context.array) item with the name "{item_name}"')
def step_impl(context, item_name):
    try:
        context.item = context.dataset.items.upload(context.array,
                                                    remote_name=item_name,
                                                    item_metadata=context.item_metadata)
    except dl.exceptions.BadRequest:
        # For Scenario: Upload illegal Numpy.NdArray item
        # In such case item is not upload and "There are no items" scansion has to be executed
        pass


@then(u'Item is correctly uploaded to platform')
def step_impl(context):
    item_get = context.dataset.items.get(item_id=context.item.id)

    for key in context.item_metadata:
        assert key in context.item.metadata
    assert item_get.id == context.item.id


@when(u'I Download as Numpy.NdArray the uploaded item')
def step_impl(context):
    context.download_array = context.item.download(save_locally=False, to_array=True)


@then(u'Download Numpy.NdArray item and context.array size equal')
# I not check numpy.array_equal since the  numpy.ndarray to io.BytesIO can the RGB values
def step_impl(context):
    assert context.download_array.size, context.array.size


@when(u'Download as Numpy.NdArray the .mp4')
def step_impl(context):
    context.download_array = context.item_mp4.download(save_locally=False, to_array=True)


@given(u'I remove log files')
def step_impl(context):
    for f in os.listdir("."):
        if any(x in f for x in ["log", ".json"]):
            os.remove(f)


@then(u'Log file is exist')
def step_impl(context):
    for f in os.listdir("."):
        if any(x in f for x in ["log", ".json"]):
            return
    assert False


@then(u'Log file does not exist')
def step_impl(context):
    for f in os.listdir("."):
        if any(x in f for x in ["log", ".json"]):
            assert False
