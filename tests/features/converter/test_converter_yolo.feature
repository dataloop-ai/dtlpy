Feature: Converter yolo format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "yolo_converter"
        And I create a dataset with a random name

    Scenario: Convert local yolo dataset to dataloop
        Given There is a local "yolo" dataset in "converter/yolo/local_dataset"
        When I convert local "yolo" dataset to "dataloop"
        Given Local path in "converter/yolo/reverse" is clean
        When I reverse dataloop dataset to local "yolo" in "converter/yolo/reverse"
        Then local "yolo" dataset in "converter/yolo/local_dataset" is equal to reversed dataset in "converter/yolo/reverse"