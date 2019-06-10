def main():
    """
    Annotate a batch of images using a model and upload to platform
    :return:
    """
    import numpy as np
    from PIL import Image
    from keras.applications.imagenet_utils import decode_predictions
    from keras.applications.inception_v3 import InceptionV3, preprocess_input

    import dtlpy as dl
    from dtlpy.utilities.annotations import ImageAnnotation

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
            print(item.filename)
            img_batch = [dataset.items.download(item_id=item.id, save_locally=False)]
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
            # create batch of annotations
            batch_annotations = list()
            for i_pred, label in enumerate(labels):
                # create platform annotations instance
                annotation = ImageAnnotation()
                # add the class labels

                ##############################
                # If model is classification #
                ##############################
                annotation.add_annotation(
                    pts=list(),  # no pts so empty list
                    label=label[0][1],  # predicted label
                    annotation_type='class'  # type of annotations is class
                )
                #############################
                # If model outputs polygons #
                #############################
                annotation.add_annotation(
                    pts=pred['polygon_pts'],  # list of list of pts. [[x0,y0], [x1,y1]... [xn,yn]]
                    label=labels[i_pred][0][1],  # predicted label
                    annotation_type='segment'  # type of annotations is class
                )
                #########################
                # If model outputs mask #
                #########################
                annotation.add_annotation(
                    pts=pred['mask'],  # binary mask of the annotation. shape as the input image to model (nxm)
                    label=labels[i_pred][0][1],  # predicted label
                    annotation_type='binary',  # type of annotations is class
                    color=pred['color'],  # need to input the class color for the platform
                    img_shape=orig_img_shape[i_pred]  # need to input the original shape so to match the platform image
                )

                # append DataLoop annotation to list
                batch_annotations.append(annotation.to_platform())
            # upload a annotations to matching items in platform
            item.annotations.upload()
