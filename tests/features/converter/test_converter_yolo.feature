Feature: Converter yolo format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "yolo_converter"
        And I create a dataset with a random name

    @testrail-C4523083
    @DAT-46491
    Scenario: Convert local yolo dataset to dataloop
        Given There is a local "yolo" dataset in "converter/yolo/local_dataset"
        When I convert local "yolo" dataset to "dataloop"
        Given Local path in "converter/yolo/reverse" is clean
        When I reverse dataloop dataset to local "yolo" in "converter/yolo/reverse"
        Then local "yolo" dataset in "converter/yolo/local_dataset" is equal to reversed dataset in "converter/yolo/reverse"

    Scenario: Upload dataset with inner folder using coco converter
        Given I use "YOLO" converter to upload items with annotations to the dataset using the given params
            | Parameter              | Value                                                           |
            | local_items_path       | converter/yolo/local_yolo_with_folders/items                    |
            | local_labels_path      | converter/yolo/local_yolo_with_folders/annotations/labels.names |
            | local_annotations_path | converter/yolo/local_yolo_with_folders/annotations/yolo         |
        And   Local path in "converter/yolo/local_downloaded_items" is clean
        And   I download the dataset items annotations in "YOLO" format using the given params
            | Parameter  | Value                                 |
            | local_path | converter/yolo/local_downloaded_items |
        Then  I use "YOLO" format to compare the uploaded annotations with the downloaded annotations
