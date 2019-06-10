Feature: Annotaions repository Delete function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "0162_annotations.json"

    Scenario: Delete annotation
        Given There is annotation x
        When I delete a annotation x
        Then Annotation x does not exist in item

    Scenario: Delete a non-existing Annotation
        When I try to delete a non-existing annotation
        Then "NotFound" exception should be raised
        And No annotation was deleted