import behave
import os
import time


@behave.given(u'I upload an item in the path "{item_path}" to the dataset')
def step_impl(context, item_path):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=context.item_path)


@behave.given(u'I upload items in the path "{items_path}" to the dataset in index "{index}"')
@behave.when(u'I upload items in the path "{items_path}" to the dataset in index "{index}"')
def step_impl(context, items_path, index):
    context.items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], items_path)
    context.datasets[int(index)].items.upload(local_path=context.items_path)


@behave.given(u'I upload an item of type "{item_type}" to the dataset')
def step_impl(context, item_type):
    items_types_list = {
        # Images
        "bmp image": os.path.join("supported_items_collection", "bmp_image_item.bmp"),
        "jfif image": os.path.join("supported_items_collection", "jfif_image_item.jfif"),
        "jpeg image": os.path.join("supported_items_collection", "jpeg_image_item.jpeg"),
        "jpg image": os.path.join("supported_items_collection", "jpg_image_item.jpg"),
        "png image": os.path.join("supported_items_collection", "png_image_item.png"),
        "tif image": os.path.join("supported_items_collection", "tif_image_item.tif"),
        "tiff image": os.path.join("supported_items_collection", "tiff_image_item.tiff"),
        "webp image": os.path.join("supported_items_collection", "webp_image_item.webp"),
        # Videos
        "3gp video": os.path.join("supported_items_collection", "3gp_video_item.3gp"),
        "avi video": os.path.join("supported_items_collection", "avi_video_item.avi"),
        "m4v video": os.path.join("supported_items_collection", "m4v_video_item.m4v"),
        "mkv video": os.path.join("supported_items_collection", "mkv_video_item.mkv"),
        "mp4 video": os.path.join("supported_items_collection", "mp4_video_item.mp4"),
        "webm video": os.path.join("supported_items_collection", "webm_video_item.webm"),
        # Audios
        "aac audio": os.path.join("supported_items_collection", "aac_audio_item.aac"),
        "flac audio": os.path.join("supported_items_collection", "flac_audio_item.flac"),
        "m4a audio": os.path.join("supported_items_collection", "m4a_audio_item.m4a"),
        "mp3 audio": os.path.join("supported_items_collection", "mp3_audio_item.mp3"),
        "ogg audio": os.path.join("supported_items_collection", "ogg_audio_item.ogg"),
        "wav audio": os.path.join("supported_items_collection", "wav_audio_item.wav"),
        # Texts
        "txt text": os.path.join("supported_items_collection", "txt_text_item.txt"),
    }

    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], items_types_list[item_type])
    context.item = context.dataset.items.upload(local_path=context.item_path, overwrite=True)

    # wait for platform attributes
    limit = 10 * 30
    stat = time.time()
    while True:
        time.sleep(3)
        context.item = context.dataset.items.get(item_id=context.item.id)
        if "video" in context.item.mimetype:
            if context.item.fps is not None:
                break
        elif "image" in context.item.mimetype and context.item.metadata['system'].get("height") is not None:
            break
        elif "image" not in context.item.mimetype and 'video' not in context.item.mimetype:
            break
        if time.time() - stat > limit:
            raise TimeoutError("Timeout while waiting for platform attributes")


@behave.given(u'I upload an item in the path "{item_path}" to "{dataset_name}"')
def step_impl(context, item_path, dataset_name):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    dataset = context.dl.datasets.get(dataset_name=dataset_name)
    context.item = dataset.items.upload(local_path=context.item_path)


@behave.when('I save the list of items as "{var_name}"')
def step_impl(context, var_name):
    items = getattr(context, 'items', None)
    assert items is not None, 'No items found in context to save.'
    ids = []
    for item in items:
        if hasattr(item, 'id'):
            ids.append(item.id)
        elif isinstance(item, dict) and 'id' in item:
            ids.append(item['id'])
        else:
            ids.append(item)
    setattr(context, var_name, ids)


@behave.then('The list "{list1}" should match the list "{list2}"')
def step_impl(context, list1, list2):
    l1 = set(getattr(context, list1))
    l2 = set(getattr(context, list2))
    assert l1 == l2, f"Lists do not match: {list1}={l1}, {list2}={l2}"
