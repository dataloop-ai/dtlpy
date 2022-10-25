Feature: Annotaions repository Get service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_get"
        And I create a dataset with a random name

    @testrail-C4523036
    Scenario: Get an existing annotation by id
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And There is annotation x
        When I get the annotation by id
        Then I receive an Annotation object
        And Annotation received equals to annotation x

    @testrail-C4523036
    Scenario: Get non-existing annotation
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        When I try to get a non-existing annotation
        Then "BadRequest" exception should be raised

