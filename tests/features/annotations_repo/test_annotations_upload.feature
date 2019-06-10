Feature: Annotations repository Upload function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"
        And Labels in file: "labels.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
    
    Scenario: Upload annotations from file
        When I upload annotations from file: "0162_annotations.json"
        Then Item should have annotations uploaded

    Scenario: Upload a single annotation
        Given There is an annotation description
        When I upload annotation description to Item
        Then Item should have annotation uploaded

    # allowing me to upload illegal annotation
    # Scenario: Upload a single annotation: illegal
    #     Given There is an illegal annotation description
    #     When I try to upload annotation description to Item
    #     Then "InternalServerError" exception should be raised
