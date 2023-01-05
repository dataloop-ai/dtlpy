import behave
import os
import glob
import shutil
import urllib.request
import base64


@behave.when(u'I download dataset to "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    context.dataset.items.download(filters=None,
                                   local_path=local_path,
                                   file_types=None,
                                   save_locally=True,
                                   annotation_options=['mask', 'instance', 'json'],
                                   with_text=False,
                                   thickness=3)


@behave.when(u'I download dataset folder "{folder_path}" to "{local_path}"')
def step_impl(context, folder_path, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    context.dataset.download_folder(folder_path=folder_path,
                                    local_path=local_path,
                                    to_items_folder=False)


@behave.when(u'I download dataset to "{local_path}" without item folder')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    context.dataset.items.download(filters=None,
                                   local_path=local_path,
                                   file_types=None,
                                   save_locally=True,
                                   annotation_options=['mask', 'instance', 'json'],
                                   with_text=False,
                                   thickness=3,
                                   to_items_folder=False)


@behave.then(u'There is no "{log}" file in folder "{download_path}"')
def step_impl(context, log, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)

    files = os.listdir(download_path)
    for file in files:
        assert log not in file


@behave.then(u'Dataset downloaded to "{download_path}" is equal to dataset in "{should_be_path}"')
def step_impl(context, download_path, should_be_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    files = os.listdir(download_path)
    excepted_dirs = ['instance', 'json', 'mask']
    for file in excepted_dirs:
        assert file in files
    assert len(files) == 4


@behave.given(u'There are no folder or files in folder "{dir_path}"')
def step_impl(context, dir_path):
    dir_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], dir_path)
    dir_path = os.path.join(dir_path, "*")

    files = glob.glob(dir_path)
    for f in files:
        if os.path.isdir(f):
            shutil.rmtree(f)
        elif os.path.isfile(f):
            os.remove(f)

    assert len(glob.glob(dir_path)) == 0


def download_images(context, path):
    # imgNum - number of images
    # imgDim - images dimension
    imgNum = int(context.num_of_items)
    imgDim = [500, 500]

    if path == 'local':
        download_path = context.local_path
    else:
        download_path = context.items_path

    context.images_sizes_list = []
    # Downloading "imgNum" images to cwd with names: "stock-image-X.jpg"
    for i in range(1, int(imgNum) + 1):
        i = str(i)
        urllib.request.urlretrieve(('https://picsum.photos/' + str(imgDim[0]) + '/' + str(imgDim[1]) + '?random'),
                                   (download_path + 'stock-image-' + i + '.' + context.type_of_images))

        with open(download_path + 'stock-image-' + i + '.' + context.type_of_images, "rb") as image_file:
            context.images_sizes_list.append(base64.b64encode(image_file.read()))


@behave.given(u'I get "{num_of_items}" images of type "{type_of_images}" for the dataset')
def step_impl(context, num_of_items, type_of_images):
    context.local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Dataset_Temp", "")
    context.num_of_items = num_of_items
    context.type_of_images = type_of_images

    try:
        os.makedirs(context.local_path)
    except:
        print("Path was created")

    download_images(context, 'local')


@behave.when(u'I upload all the images for the dataset')
def step_impl(context):
    context.dataset.items.upload(local_path=context.local_path)


@behave.when(u'I download the dataset without Overwrite variable')
def step_impl(context):
    try:
        os.makedirs(context.local_path)
    except:
        print("Path was created")

    context.dataset.items.download(local_path=context.local_path)

    context.overwritten_images_sizes_list = []

    with open(context.local_path + '/items/stock-image-1.png', "rb") as image_file:
        context.overwritten_images_sizes_list.append(base64.b64encode(image_file.read()))


@behave.when(u'I download the dataset with Overwrite "{overwrite_status}"')
def step_impl(context, overwrite_status):
    if overwrite_status == "True":
        context.dataset.items.download(local_path=context.local_path, overwrite=True)
    else:
        context.dataset.items.download(local_path=context.local_path, overwrite=False)

    with open(context.local_path + '/items/stock-image-1.png', "rb") as image_file:
        context.overwritten_images_sizes_list.append(base64.b64encode(image_file.read()))


@behave.when(u'I modify the downloaded item')
def step_impl(context):
    context.items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Dataset_Temp/items", "")
    num_of_items = 1
    type_of_images = "png"

    # imgNum - number of images
    # imgDim - images dimension
    imgNum = int(num_of_items)
    imgDim = [500, 500]

    download_images(context, 'items')


@behave.then(u'The dataset item will be "{is_overwritten}"')
def step_impl(context, is_overwritten):
    if is_overwritten == "overwritten":
        assert str(context.overwritten_images_sizes_list[1]) == str(context.overwritten_images_sizes_list[0])
        assert str(context.overwritten_images_sizes_list[1]) != str(context.images_sizes_list[0])
    else:
        assert str(context.overwritten_images_sizes_list[1]) != str(context.overwritten_images_sizes_list[0])
        assert str(context.overwritten_images_sizes_list[1]) == str(context.images_sizes_list[0])

    shutil.rmtree(os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Dataset_Temp"))


@behave.then(u'The folder "{download_path}" is equal to to "{should_be_path}"')
def step_impl(context, download_path, should_be_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)
    files = os.listdir(download_path)
    excepted_dirs = os.listdir(should_be_path)
    for file in excepted_dirs:
        assert file in files
