def main():
    import dtlpy as dl
    import matplotlib.pyplot as plt

    # Get project and dataset
    project = dl.projects.get(project_name='Food')
    dataset = project.datasets.get(dataset_name='BeansDataset')
    item = dataset.items.get(filepath='/flying boxes.mp4')

    ############################
    # using annotation builder #
    ############################
    # create annotation builder
    builder = item.annotations.builder()

    for i_frame in range(100):
        # go over 100 frame
        for i_detection in range(10):
            # for each frame we have 10 different detections (location is just for the example)
            builder.add(annotation_definition=dl.Box(top=2 * i_frame,
                                                     left=2 * i_detection,
                                                     bottom=2 * i_frame + 10,
                                                     right=2 * i_detection + 100,
                                                     label="moving box"),
                        frame_num=i_frame,  # set the frame for the annotation
                        object_id=i_detection + 1
                        # need to input the element id to create the connection between frames
                        )
            # starting from frame 50 add another 10 new annotations of a moving point
            if i_frame > 50:
                builder.add(annotation_definition=dl.Point(x=2 * i_frame,
                                                           y=2 * i_detection,
                                                           label="moving point"),
                            frame_num=i_frame,
                            object_id=20 + (i_detection + 1))
    # get frame annotations
    frame_annotations = builder.get_frame(frame_num=55)
    # Plot the annotations in frame 55 of the created annotations
    plt.figure()
    plt.imshow(frame_annotations.show())

    # plot each annotations separately
    for annotation in frame_annotations:
        plt.figure()
        plt.imshow(annotation.show())
        plt.title(annotation.label)

    # Add the annotations to platform
    item.annotations.upload(builder)

    #####################
    # single annotation #
    #####################
    # create one annotations for a video (without using tracker and object ids)
    annotation = dl.Annotation.new(item=item)

    for i_frame in range(100):
        # go over 100 frame
        annotation.add_frame(annotation_definition=dl.Box(top=2 * i_frame,
                                                          left=2 * (i_frame + 10),
                                                          bottom=2 * (i_frame + 50),
                                                          right=2 * (i_frame + 100),
                                                          label="moving box",
                                                          ),
                             frame_num=i_frame,  # set the frame for the annotation
                             )

    # upload to platform
    annotation.upload()

    ##############################################
    # show annotation state in a specified frame #
    ##############################################

    # Get from platform
    annotations = item.annotations.list()

    # Plot the annotations in frame 55 of the created annotations
    plt.figure()
    plt.imshow(annotations.get_frame(frame_num=55).show())

    # Play video with the Dataloop video player
    annotations.video_player()
