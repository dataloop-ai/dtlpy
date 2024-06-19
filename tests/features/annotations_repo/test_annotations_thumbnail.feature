Feature: Item Annotations thumbnail

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "annotation_thumbnail"
    And I create a dataset with a random name


  @DAT-71001
  Scenario: Show annotation thumbnail - Should create thumbnail v2 on item
    When I upload item in "0000000162.jpg"
    And I annotate item
    And I Show annotation thumbnail for the item
    Then I should see a thumbnail v2 on the item

  @DAT-71001
  Scenario: Show annotation thumbnail after update - Should create new thumbnail v2 on item
    When I upload item in "0000000162.jpg"
    And I annotate item
    And I Show annotation thumbnail for the item
    And I update annotation label with new name "edited"
    And I Show annotation thumbnail for the item
    Then I should see a thumbnail v2 on the item

  @DAT-71001
  Scenario: Show annotation thumbnail after delete - Should delete the thumbnail v2 from the item
    When I upload item in "0000000162.jpg"
    And I annotate item
    And I Show annotation thumbnail for the item
    And I delete annotation
    And I Show annotation thumbnail for the item
    Then I should not see a thumbnail v2 on the item

  @DAT-71001
  Scenario: Show annotation thumbnail after delete and add - Should create new thumbnail v2 on item
    When I upload item in "0000000162.jpg"
    And I annotate item
    And I Show annotation thumbnail for the item
    And I delete annotation
    And I Show annotation thumbnail for the item
    And I annotate item
    And I Show annotation thumbnail for the item
    Then I should see a thumbnail v2 on the item

