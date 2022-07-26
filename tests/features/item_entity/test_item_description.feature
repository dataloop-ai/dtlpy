Feature: Item description testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project1"
        And I create a dataset with a random name
        And Item in path "0000000162.jpg" is uploaded to "Dataset"


    @testrail-C4532161
    Scenario: Add description to item
        When  I Add description "Item description" to item
        Then  I validate item.description annotation