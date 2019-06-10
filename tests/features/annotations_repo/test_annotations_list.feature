Feature: Annotaions repository List function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"

    Scenario: List all annotations when no annotations exists
        Given There are no annotations
        When I list all annotations
        Then I receive an empty annotations list

    Scenario: List all annotations when annotations exist
        Given Item is annotated with annotations in file: "0162_annotations.json"
        When I list all annotations
        Then I receive a list of all annotations
        And The annotations in the list equals the annotations uploaded