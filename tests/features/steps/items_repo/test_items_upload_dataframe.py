import behave
import os
import cv2
import pandas


@behave.when(u'I upload item using data frame from "{upload_path}"')
def step_impl(context, upload_path):
    upload_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], upload_path)

    # get filepathes
    filepaths = list()
    # go over all file and run ".feature" files
    count = 0
    for path, subdirs, files in os.walk(upload_path):
        for filename in files:
            striped, ext = os.path.splitext(filename)
            if ext in ['.jpg', '.png']:
                filepaths.append({'local_path': os.path.join(path, filename),
                                  'item_metadata': {'user':
                                                        {'dummy': count}}})
                count += 1

    df = pandas.DataFrame(filepaths)
    context.dataset.items.upload(local_path=df)


@behave.then(u'Items should have metadata')
def step_impl(context):
    items = context.dataset.items.get_all_items()
    for item in items:
        try:
            item.metadata['user']['dummy']
        except Exception:
            assert False
