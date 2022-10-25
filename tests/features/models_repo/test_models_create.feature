Feature: Models repository create testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"

  @testrail-C4523165
  Scenario: Create a model with a legal name
    When I push "first" package
      |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|type=ml|
    And I create a model with a random name
    Then Model object with the same name should be exist
    And Model object with the same name should be exist in host

  @testrail-C4523165
  Scenario: Create a model with an existing model name
    When I push "first" package
      |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|type=ml|
    And There are no models
    And I create a model with a random name
    When I create a model with the same name
    Then "BadRequest" exception should be raised
#        And "Model name must be unique in model" in error message
    And "models already exist, Model with this name already exists" in error message
    And No model was created

  @testrail-C4523165
  Scenario: Rename model entity
    When I push "first" package
      |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|type=ml|
    And I create a model with a random name
    When I rename model to "some_other_name"
    Then model name is "some_other_name"
