from behave import given, then, when
import os
import urllib.request
import shutil
import base64


@given(u'I get "{num_of_items}" images of type "{type_of_images}"')
def step_impl(context, num_of_items, type_of_images):
    context.local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Temp", "")
    context.num_of_items = num_of_items
    context.type_of_images = type_of_images

    try:
        os.makedirs(context.local_path)
    except:
        print("Path was created")

    # imgNum - number of images
    # imgDim - images dimension
    imgNum = int(num_of_items)
    imgDim = [500, 500]

    context.images_sizes_list = []
    # Downloading "imgNum" images to cwd with names: "stock-image-X.jpg"
    for i in range(1, int(imgNum) + 1):
        i = str(i)
        urllib.request.urlretrieve(('https://picsum.photos/' + str(imgDim[0]) + '/' + str(imgDim[1]) + '?random'),
                                   (context.local_path + 'stock-image-' + i + '.' + type_of_images))

        with open(context.local_path + 'stock-image-' + i + '.' + type_of_images, "rb") as image_file:
            context.images_sizes_list.append(base64.b64encode(image_file.read()))


@when(u'I upload all the images')
def step_impl(context):
    context.dataset.items.upload(local_path=context.local_path)


@when(u'I download all the images')
def step_impl(context):
    context.dataset.items.download(local_path=context.local_path)


@then(u'The images werent changed')
def step_impl(context):
    items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Temp/items", "")
    context.downloaded_images_sizes_list = []

    for i in range(1, int(context.num_of_items) + 1):
        i = str(i)

        with open(items_path + 'stock-image-' + i + '.' + context.type_of_images, "rb") as image_file:
            context.downloaded_images_sizes_list.append(base64.b64encode(image_file.read()))

    shutil.rmtree(os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Temp"))

    for i in range(0, int(context.num_of_items)):
        assert str(context.downloaded_images_sizes_list[int(i)]) == str(context.images_sizes_list[int(i)])


@when(u'I overwrite "{num_of_items}" images of type "{type_of_images}"')
def step_impl(context, num_of_items, type_of_images):
    context.num_of_items = num_of_items
    context.type_of_images = type_of_images

    try:
        os.makedirs(context.local_path)
    except:
        print("Path was created")

    # imgNum - number of images
    # imgDim - images dimension
    imgNum = int(num_of_items)
    imgDim = [500, 500]

    context.overwritten_images_sizes_list = []
    # Downloading "imgNum" images to cwd with names: "stock-image-X.jpg"
    for i in range(1, int(imgNum) + 1):
        i = str(i)
        urllib.request.urlretrieve(('https://picsum.photos/' + str(imgDim[0]) + '/' + str(imgDim[1]) + '?random'),
                                   (context.local_path + 'stock-image-' + i + '.' + type_of_images))

        with open(context.local_path + 'stock-image-' + i + '.' + type_of_images, "rb") as image_file:
            context.overwritten_images_sizes_list.append(base64.b64encode(image_file.read()))


@when(u'I download the item with Overwrite "{overwrite_status}"')
def step_impl(context, overwrite_status):
    items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Temp", "")
    item = context.dataset.items.get(filepath="/stock-image-1." + context.type_of_images)

    context.downloaded_images_sizes_list = []

    if overwrite_status == "True":
        context.file_path = item.download(local_path=items_path, overwrite=True, to_items_folder=False)
    else:
        item.download(local_path=items_path, overwrite=False, to_items_folder=False)

    with open(items_path + 'stock-image-1' + '.' + context.type_of_images, "rb") as image_file:
        context.downloaded_images_sizes_list.append(base64.b64encode(image_file.read()))


@when(u'I download the item with Overwrite value "{overwrite_status}" to path "{file_path}"')
def step_impl(context, overwrite_status, file_path):
    items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    if overwrite_status == "True":
        context.download_path = context.item.download(local_path=items_path, overwrite=True)
    else:
        context.download_path = context.item.download(local_path=items_path, overwrite=False)


@then(u'check that the new download will be with the same path "{file_path}"')
def step_impl(context, file_path):
    items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    download_path = context.item.download(local_path=items_path, overwrite=True)
    shutil.rmtree(items_path)
    assert context.download_path == download_path, "The download path is not the same as the previous one"


@then(u'The images will be "{is_overwritten}"')
def step_impl(context, is_overwritten):
    if is_overwritten == "overwritten":
        assert str(context.downloaded_images_sizes_list[0]) == str(context.images_sizes_list[0])
        assert str(context.downloaded_images_sizes_list[0]) != str(context.overwritten_images_sizes_list[0])
    else:
        assert str(context.downloaded_images_sizes_list[0]) != str(context.images_sizes_list[0])
        assert str(context.downloaded_images_sizes_list[0]) == str(context.overwritten_images_sizes_list[0])

    shutil.rmtree(os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "Upload_Download_Temp"))
