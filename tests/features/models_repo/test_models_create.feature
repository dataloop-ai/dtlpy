Feature: Models repository create testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"

  @testrail-C4523165
  @DAT-46548
  Scenario: Create a model with a legal name
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model with a random name
    Then Model object with the same name should be exist
    And Model object with the same name should be exist in host

  @testrail-C4523165
  @DAT-46548
  Scenario: Create a model with an existing model name
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And There are no models
    And I create a model with a random name
    When I create a model with the same name
    Then "BadRequest" exception should be raised
#        And "Model name must be unique in model" in error message
    And "models already exist, Model with this name already exists" in error message
    And No model was created

  @testrail-C4523165
  @DAT-46548
  Scenario: Rename model entity
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model with a random name
    When I rename model to "some_other_name"
    Then model name is "some_other_name"
    Then "model" has updatedBy field

  @DAT-44734
  Scenario: Create a two models with the same bot
    When I push "first" package
      |codebase_id=None|package_name=test-package|src_path=package_module|inputs=None|outputs=None|type=ml|modules=no_input|
    And I create a model with a random name
    And I update model status to "trained"
    And I deploy the model
    And I create a model with a random name
    And I train the model
    Then The project have only one bot

  @DAT-44695
  Scenario: delete clone model artifact
    When I push "first" package
      | codebase_id=None | package_name=test-package-clone | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model with a random name
    Then Model object with the same name should be exist
    When I upload an artifact "0000000162.jpg" to the model
    And I clone the model
    And I delete the clone model
    Then artifact is exist in the host

  @DAT-45101
  Scenario: Create a model without dataset
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model without dataset
    Then Model object with the same name should be exist
    And Model object with the same name should be exist in host

  @DAT-45099
  Scenario: Create a model with filter
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model with a random name
    Then Model filter should not be empty

  @DAT-45099
  Scenario: Create a model without filter
    When I push "first" package
      | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
    And I create a model without filter
    And I train the model
    Then "BadRequest" exception should be raised
