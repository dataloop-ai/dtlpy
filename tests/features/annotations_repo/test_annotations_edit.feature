Feature: Annotaions repository update service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_annotations_edit"
        And I create a dataset with a random name

    @testrail-C4523035
    Scenario: Updateing annotations: remove attributes
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And I remove annotations attributes
        When I update annotations
        Then  Item annotations has no attributes

    @testrail-C4523035
    Scenario: Updateing annotations: change label
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And I change all annotations labels to "person"
        When I update annotations
        Then  All item annotations have label "person"

    #TODO - not working as expected - server returns 200
    # Scenario: Updateing annotations: change to non-existing label
    #     Given I change all annotations labels to "non_existing_label"
    #     When I try to update annotations
    #     Then  "InternalServerError" exception should be raised

    @testrail-C4523035
    Scenario: Updateing annotation: change single annotation
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And There is annotation x
        And I change annotation values
        When I update annotation
        Then Annotation should be updated

    @testrail-C4523035
    Scenario: Updateing annotations: change coordinates
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And There are no files in folder "downloaded_annotations"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And There is annotation x
        And I add "50" to annotation coordinates
        When I update annotation
        Then Annotation x coordinates should be changed accordingly


