Feature: Converter voc format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "voc_converter"
        And I create a dataset with a random name

    @testrail-C4523082
    @DAT-46490
    Scenario: Convert local voc dataset to dataloop
        Given There is a local "voc" dataset in "converter/voc/local_dataset_attr"
        When I convert local "voc" dataset to "dataloop"
        Given Local path in "converter/voc/reverse" is clean
        When I reverse dataloop dataset to local "voc" in "converter/voc/reverse"
        Then local "voc" dataset in "converter/voc/local_dataset_attr" is equal to reversed dataset in "converter/voc/reverse"

    @testrail-C4523082
    @DAT-46490
    Scenario: Upload dataset with inner folder using coco converter
        Given I use "VOC" converter to upload items with annotations to the dataset using the given params
            | Parameter              | Value                                                |
            | local_items_path       | converter/voc/local_voc_with_folders/items           |
            | local_annotations_path | converter/voc/local_voc_with_folders/annotations/voc |
        And   Local path in "converter/voc/local_downloaded_items" is clean
        And   I download the dataset items annotations in "VOC" format using the given params
            | Parameter  | Value                                |
            | local_path | converter/voc/local_downloaded_items |
        Then  I use "VOC" format to compare the uploaded annotations with the downloaded annotations
