def main():
    import dtlpy as dl

    dataset = dl.projects.get("project_name").datasets.get("dataset_name")

    ############################
    # convert annotations list #
    ############################

    # convert from dataloop to other formats #
    ##########################################

    # known format #

    item = dataset.items.get(item_id="item_id")
    annotations = item.annotations.list()
    converter = dl.Converter()
    converted_annotations = converter.convert(annotations=annotations,
                                              from_format='dataloop',
                                              to_format='yolo')

    # custom format #

    # custom conversion function
    # converts 1 dataloop annotation to custom format annotation
    # returns converted annotation
    def my_converter(annotation):
        """
        :param annotation: dataloop Annotation object
        :return: format of new annotation
        """
        ann = {'label': annotation.label, 'type': annotation.type}
        return ann

    converted_annotations = converter.convert(annotations=annotations,
                                              from_format='dataloop',
                                              to_format='my_format',
                                              conversion_func=my_converter)

    # convert from other formats to dataloop format #
    #################################################

    # known format #

    # load yolo annotations from file
    annotations = list()
    with open('annotations_filepath.txt', 'r') as f:
        line = f.readline()
        while line:
            annotations.append(line)
            line = f.readline()

    # create converter object
    converter = dl.Converter()

    # convert
    converted_annotations = converter.convert(annotations=annotations,
                                              from_format='yolo',
                                              to_format='dataloop')

    # custom format #

    # load yolo annotations from file
    annotations = list()
    with open('annotations_filepath.txt', 'r') as f:
        line = f.readline()
        while line:
            annotations.append(line)
            line = f.readline()

    # create converter object
    converter = dl.Converter()

    # custom conversion function
    # converts 1 custom annotation to dataloop annotation
    # dataloop annotation
    def my_converter(annotation):
        """
        :param annotation: custom annotation format
        :type annotation: dict
        :return: dataloop Annotation object
        """
        annotations = dl.Annotation.new(annotation_definition=dl.Box(top=annotation['top'],
                                                                     bottom=annotation['bottom'],
                                                                     left=annotation['left'],
                                                                     right=annotation['right'],
                                                                     label=annotation['label']))

        return annotation

    converted_annotations = converter.convert(annotations=annotations,
                                              from_format='my_format',
                                              to_format='dataloop',
                                              conversion_func=my_converter)

    ###############################
    # convert dataset annotations #
    ###############################

    # known format #
    ################

    converter = dl.Converter()

    converter.save_to_format = 'json'
    converter.convert_dataset(dataset=dataset,
                              to_format='coco',
                              local_path='some/local/path/to/download/converted/annotations')

    # custom format #
    #################

    def my_converter(annotation):
        """
        :param annotation: dataloop Annotation object
        :return: format of new annotation
        """
        ann = {'label': annotation.label, 'type': annotation.type}
        return ann

    converter = dl.Converter()

    converter.save_to_format = 'json'
    converter.convert_dataset(dataset=dataset,
                              to_format='my_format',
                              conversion_func=my_converter,
                              local_path='some/local/path/to/download/converted/annotations')

    ################
    # save to file #
    ################

    item = dataset.items.get(item_id="item_id")
    annotations = item.annotations.list()
    converter = dl.Converter()
    converter.convert(annotations=annotations,
                      from_format='dataloop',
                      to_format='yolo')

    # what file format to save to
    converter.save_to_format = '.txt'
    # save
    converter.save_to_file(save_to='local_path', to_format='yolo')
