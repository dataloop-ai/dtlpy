Feature: Datasets repository - Export datasets

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "export_datasets_testing"
    And I create a dataset with a random name

  @DAT-90470
  Scenario: Fetch the export status history for a failed export dataset
    When There are "10" items
    And I create "delete_me" folder
    When I Exporting the dataset
    And I wait "1"
    Then I check if created folder is empty
    When I delete the dataset that was created by name
    And I wait "2"
    Then I check if created folder is empty
    When I send "post" request with "/datasets/exports" and params
      | key       | value      |
      | sortOrder | ASC        |
      | sortBy    | createdAt  |
      | projects  | project.id |
      | datasetId | dataset.id |
    Then I expect status will be "failed"
    Then delete the folder and its content
