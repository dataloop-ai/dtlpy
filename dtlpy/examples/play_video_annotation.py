def run():
    """
    Play a video from platform with annotations in the Dataloop python player
    :return:
    """
    from dtlpy.utilities.videos.video_player import VideoPlayer
    project_name = 'Dancing'
    dataset_name = 'Flossing'
    item_name = '/first_try.mp4'

    VideoPlayer(project_name=project_name,
                dataset_name=dataset_name,
                item_filepath=item_name)
