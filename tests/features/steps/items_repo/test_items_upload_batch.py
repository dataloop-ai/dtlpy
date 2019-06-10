import behave
import os
import cv2


@behave.when(u'I upload item batch from "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    context.dataset.items.upload_batch(filepaths=local_path,
                                       remote_path=None,
                                       upload_options=None)


@behave.then(u'Items in "{download_path}" should equal items in "{upload_path}"')
def step_impl(context, download_path, upload_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    upload_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], upload_path)

    download_list = os.listdir(download_path)
    upload_list = os.listdir(upload_path)
    assert len(download_list) == len(upload_list)

    for item in download_list:
        original = cv2.imread(os.path.join(upload_path, item))
        downloaded = cv2.imread(os.path.join(download_path, item))
        if original.shape == downloaded.shape:
            difference = cv2.subtract(original, downloaded)
            b, g, r = cv2.split(difference)
            if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
                assert True
            else:
                assert False
        else:
            assert False
