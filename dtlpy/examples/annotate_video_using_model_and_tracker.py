def main():
    """
    Detect and track (using model and some tracker) and upload annotation to platform
    :return:
    """
    import cv2
    import dtlpy as dl

    ##########################
    # Load model and tracker #
    ##########################
    # load your model for detection
    model = load_some_model()
    # load any tracking algorithm to track detected elements
    tracker = load_some_tracker()

    ##############
    # load video #
    ##############
    video_path = 'some/video/path'

    vid = cv2.VideoCapture(video_path)
    if not vid.isOpened():
        raise IOError("Couldn't open webcam or video")
    video_fps = vid.get(cv2.CAP_PROP_FPS)
    video_size = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    video_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

    ############
    # Platform #
    ###########
    # get the item from platform
    item = dl.projects.get(project_name='MyProject') \
        .datasets.get(dataset_name='MyDataset') \
        .items.get(filepath='/path/to/video.mp4')
    builder = item.annotations.builder()

    #######
    # Run #
    #######
    frame_num = 0
    while True:
        # get new frame from video
        return_value, frame = vid.read()
        if not return_value:
            break

        # get detection
        detections = model.predict(frame)

        # update tracker
        tracked_elements = tracker.update(detections, frame)

        # update annotations object
        for element in tracked_elements:
            # element.bb - format of the bounding box is 2 points in 1 array - [x_left, y_top, x_right, y_bottom])
            # tracking id of each element is in element.id. to keep the ids of the detected elements
            left, top, bottom, right = element.bb,  # points bounding box annotation
            builder.add(annotation_definition=dl.Box(top=top,
                                                     left=left,
                                                     right=right,
                                                     bottom=bottom,
                                                     label=element.label),
                        object_id=element.id,
                        frame_num=frame_num)
        # increase frame number
        frame_num += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    ##################################
    # Upload annotations to platform #
    ##################################
    item.annotations.upload(builder.to_platform())
