def run():
    """
    Play a video from platform with annotations in the Dataloop python player
    :return:
    """
    from dtlpy.utilities.videos.video_player import VideoPlayer
    project_name = 'MyProject'
    dataset_name = 'MyDataset'
    item_name = '/filename.mp4'

    a = VideoPlayer(project_name=project_name,
                    dataset_name=dataset_name,
                    item_filepath=item_name)
