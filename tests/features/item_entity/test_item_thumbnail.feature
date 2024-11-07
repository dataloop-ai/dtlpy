Feature: Item thumbnail feature testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "item-thumbnail"
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"


  @DAT-56167
  Scenario: Update item thumbnail to null > open item thumbnail - Should get new thumbnail
    When I get an item thumbnail response
    And I get item thumbnail id
    And I update item "metadata.system.thumbnailId" with "None" system_metadata "True"
    Then I get an item thumbnail response
    And I validate item thumbnail id is "not-equal" to the previous thumbnail id

