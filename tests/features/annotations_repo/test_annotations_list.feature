Feature: Annotaions repository List service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_list"
        And I create a dataset with a random name

    @testrail-C4523037
    @DAT-46431
    Scenario: List all annotations when no annotations exists
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no annotations
        When I list all annotations
        Then I receive an empty annotations list

    @testrail-C4523037
    @DAT-46431
    Scenario: List all annotations when annotations exist
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        When I list all annotations
        Then I receive a list of all annotations
        And The annotations in the list equals the annotations uploaded

