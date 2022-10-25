@frozen_dataset
Feature: Datasets repository readonly mode testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_readonly"

    @testrail-C4523090
    Scenario: Set dataset readonly mode to True
        Given There are no datasets
        And I create a dataset with a random name
        When I set dataset readonly mode to "True"
        Then Dataset is in readonly mode

    @testrail-C4523090
    Scenario: Set and unset readonly mode
        Given There are no datasets
        And I create a dataset with a random name
        When I set dataset readonly mode to "True"
        Then Dataset is in readonly mode
        When I set dataset readonly mode to "False"
        Then Dataset is not in readonly mode
        When I set dataset readonly mode to "True"
        Then Dataset is in readonly mode
        When I set dataset readonly mode to "False"
        Then Dataset is not in readonly mode
