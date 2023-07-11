Feature: command Entity repo - test using dataset clone feature

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "command_test"
        And I create a dataset with a random name

    @testrail-C4523079
    @DAT-46487
    Scenario: Use command with clone dataset
        Given There are "10" items
        When Dataset is cloning
        Then Cloned dataset has "10" items

    @testrail-C4523079
    @DAT-46487
    Scenario: command error  with clone dataset with same name
        When Dataset is cloning with same name get already exist error

