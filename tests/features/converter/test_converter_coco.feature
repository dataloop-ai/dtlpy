Feature: Converter coco format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "coco_converter"
        And I create a dataset with a random name

    @testrail-C4523080
    Scenario: Convert local coco dataset to dataloop
        Given There is a local "coco" dataset in "converter/coco/local_dataset"
        When I convert local "coco" dataset to "dataloop"
        Given Local path in "converter/coco/reverse" is clean
        When I reverse dataloop dataset to local "coco" in "converter/coco/reverse"
        Then local "coco" dataset in "converter/coco/local_dataset" is equal to reversed dataset in "converter/coco/reverse"

    @testrail-C4523080
    Scenario: Convert local coco dataset with inner folders to dataloop
        Given There is a local "coco" dataset in "converter/coco/local_dataset_inner"
        When I convert local "coco" dataset to "dataloop"
        Given Local path in "converter/coco/reverse" is clean
        When I reverse dataloop dataset to local "coco" in "converter/coco/reverse"
        Then local "coco" dataset in "converter/coco/local_dataset_inner" is equal to reversed dataset in "converter/coco/reverse"