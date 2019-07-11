def main():
    """
        Annotate a batch of images using a model and upload to platform
        :return:
        """
    import numpy as np
    from PIL import Image
    from keras.applications.imagenet_utils import decode_predictions
    from keras.applications.inception_v3 import InceptionV3, preprocess_input
    from dtlpy.utilities.annotations import ImageAnnotation
    import dtlpy as dl

    ##############
    # load model #
    ##############
    model = InceptionV3()

    ##########################
    # init platform instance #
    ##########################
    project = dl.projects.get(project_name='ImageNet')
    dataset = project.datasets.get(dataset_name='sample')

    # get pages of images from dataset
    pages = dataset.items.list()
    ####################
    # start annotating #
    ####################
    for page in pages:
        for item in page:
            if item.type == 'dir':
                continue
            img_batch = [item.download(save_locally=False)]
            # load images
            img_batch = [Image.open(buf) for buf in img_batch]
            # get original images shapes before reshaping for model
            orig_img_shape = [img.size[::-1] for img in img_batch]
            # reshape and load images
            batch = np.array([np.array(img.resize((299, 299))) for img in img_batch])
            # preprocess batch
            batch = preprocess_input(batch)
            # inference the model
            predictions = model.predict(batch)
            # get ImageNet labels
            labels = decode_predictions(predictions, top=1)
            # create platform annotations instance
            builder = item.annotations.builder()
            for i_pred, label in enumerate(labels):

                # add the class labels
                ##############################
                # If model is classification #
                ##############################
                builder.add(annotation_definition=dl.Classification(label=label[0][1]))
                #############################
                # If model outputs polygons #
                #############################
                builder.add(annotation_definition=dl.Polyline(geo=pred['polygon_pts'],
                                                              label=labels[i_pred][0][1]))
                #########################
                # If model outputs mask #
                #########################
                builder.add(annotation_definition=dl.Segmentation(geo=pred['mask'],
                                                                  label=labels[i_pred][0][1]))
            # upload a annotations to matching items in platform
            builder.upload()
