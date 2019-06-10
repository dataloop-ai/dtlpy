Feature: Annotaions repository Get function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "0162_annotations.json"

    Scenario: Get an existing annotation by id
        Given There is annotation x
        When I get the annotation by id
        Then I receive an Annotation object
        And Annotation received equals to annotation x

    Scenario: Get non-existing annotation
        When I try to get a non-existing annotation
        Then "InternalServerError" exception should be raised