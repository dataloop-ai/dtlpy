Feature: Datasets repository lists testing

  Background: Initiate Platform Interface and create a project with datasets
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "datasets_list"
    And Create "5" datasets in project with the prefix name "test"

  @DAT-67880
  Scenario:  Get dataset from list by dataset_name
    When I get datasets list by params
      | name=test-2 |
    Then I receive a datasets list of "1" dataset

  @DAT-58070
  Scenario:  Get dataset from list by creator
    When I get datasets list by params
      | creator=current_user |
    Then I receive a datasets list of "5" dataset

  @DAT-67881
  Scenario:  Get dataset from list by filter metadata
    When I get dataset by name "test-1"
    And I update dataset metadata "user.test:'5'"
    When I create dataset filters by metadata - "user.test" = "5"
    And I get datasets list by params
      | filters=context.filters |
    Then I receive a datasets list of "1" dataset

  @DAT-67882
  Scenario:  Get dataset from list by dataset_name , creator and filter
    When I get dataset by name "test-4"
    And I update dataset metadata "user.test:'3'"
    When I create dataset filters by metadata - "user.test" = "3"
    When I get datasets list by params
      | filters=context.filters | name=test-4 | creator=current_user |
    Then I receive a datasets list of "1" dataset

