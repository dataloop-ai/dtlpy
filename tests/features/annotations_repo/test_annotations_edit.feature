Feature: Annotaions repository update service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_edit"
        And I create a dataset with a random name

    @testrail-C4523035
    @DAT-46426
    Scenario: Updateing annotations: remove attributes
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And I remove annotations attributes
        When I update annotations
        Then  Item annotations has no attributes

    @testrail-C4523035
    @DAT-46426
    Scenario: Updateing annotations: start and end time
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And There is annotation x
        And I set start frame to "20" and end frame to "70"
        When I update annotation
        Then annotation x metadata should be changed accordingly



