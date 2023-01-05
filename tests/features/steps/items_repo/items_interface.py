import behave
import os


@behave.given(u'I upload an item in the path "{item_path}" to the dataset')
def step_impl(context, item_path):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=context.item_path)


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


@behave.given(u'I upload an item in the path "{item_path}" to "{dataset_name}"')
def step_impl(context, item_path, dataset_name):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    dataset = context.dl.datasets.get(dataset_name=dataset_name)
    context.item = dataset.items.upload(local_path=context.item_path)
