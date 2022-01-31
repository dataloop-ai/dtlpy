Feature: Snapshot repository query testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "models_list"
        And There is a dataset by the name of "snapshots_dataset"

    @testrail-C4525320
    Scenario: List by model name
        Given I create "1" models
        And I create "6" snapshots
        When I list snapshots with filter field "name" and values "snapshot-num-1"
        Then I get "1" entities

