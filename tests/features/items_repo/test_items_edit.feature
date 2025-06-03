Feature: Items repository update service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "items_edit"
    And I create a dataset with a random name
    And There is an item

  @testrail-C4523115
  @DAT-46536
  Scenario: Update items name
    When I update items name to "/test_name.jpg"
    Then I receive an Item object with name "/test_name.jpg"
    And Item in host was changed to "/test_name.jpg"
    And Only name attributes was changed

  @testrail-C4523115
  @DAT-46536
  Scenario: Update items path
    Given And There is an item by the name of "/test_item.jpg"
    When I update items name to "/folder/test_item.jpg"
    Then I receive an Item object with name "/folder/test_item.jpg"
    And Item in host was changed to "/folder/test_item.jpg"
    And PageEntity has directory item "/folder"

  @testrail-C4523115
  @DAT-46536
  Scenario: Update item system metadata - with param system_metadata=True
    When I update item system metadata with system_metadata="True"
    Then Then I receive an Item object
    And Item in host has modified metadata
    And Only metadata was changed

  @testrail-C4523115
  @DAT-46536
  Scenario: Update item system metadata - with param system_metadata=False
    When I update item system metadata with system_metadata="False"
    Then Then I receive an Item object
    And Item in host was not changed


  @DAT-80521
  Scenario: Update item using update_values without filters - Should return error
    When I try to update item with params
      | key  | value |
      | item | None  |
    Then I receive error with status code "400"
    And "must provide either item or filters" in error message

  @DAT-80521
  Scenario: Update item using system_update_values without filters - Should return error
    When I try to update item with params
      | key           | value     |
      | update_values | {"a":"b"} |
    Then I receive error with status code "400"
    And "Cannot provide "update_values" or "system_update_values" with a specific "item" for an individual update." in error message

  @DAT-80700
  Scenario: Update item with system_update_values without system_metadata true - Should not update system
    When I create filters
    And I add field "annotated" with values "False" and operator "None"
    When I try to update item with params
      | key                  | value           |
      | item                 | None            |
      | filters              | context.filters |
      | system_update_values | {"c":"d"}       |
    Then I validate "{"c":"d"}" not in item system metadata

  @DAT-80701
  Scenario: Update item with update_values and system_update_values and system_metadata true - Should update item
    When I create filters
    And I add field "annotated" with values "False" and operator "None"
    When I try to update item with params
      | key                  | value           |
      | item                 | None            |
      | filters              | context.filters |
      | update_values        | {"a":"b"}       |
      | system_update_values | {"c":"d"}       |
      | system_metadata      | True            |
    Then I validate for "item" that the updated metadata is "user.a:b"
    Then I validate for "item" that the updated metadata is "system.c:d"

  @skip_test
  @DAT-94062
  @DM-cache
  Scenario: Update items name twice at the same time
    When I update items name to "/test_name.jpg" and "/test_name2.jpg" at the same time
    Then I receive an Item object with names "/test_name.jpg" or "/test_name2.jpg"
    And Item in host was changed to name "/test_name.jpg" or "/test_name2.jpg"
    And Only name attributes was changed
