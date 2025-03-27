@ATP @AIRGAPPED
Feature: Model Management testing


  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_management_flow"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item


  @DAT-79934
  Scenario: Model Management flow - Pre-trained model ,Train, Deploy, Predict
    """
    ##   Steps for global Model app
    #    When I get global dpk by name "yolov9-offline"
    #    And I install the app using the global dpk
    """
    Then Add Multiple Labels "person", "car", "stop sign"
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    When I publish a dpk to the platform
    And I install the app
    And I fetch the model by the name "test-model"
    And I prepare model for training
    When I "train" the model
    Then service metadata has a model id and operation "train"
    Then model status should be "trained" with execution "True" that has function "train_model"
    When I "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When I "evaluate" the model
    Then service metadata has a model id and operation "evaluate"
    Then model status should be "deployed" with execution "True" that has function "evaluate_model"
    And Dataset has a scores file
    When I call the precision recall api
    Then Log "Running function: train_model" is in model.log() with operation "train"
    Then Log "Running function: evaluate_model" is in model.log() with operation "evaluate"
    Then I clean the project

  @DAT-79935
  Scenario: Model Management flow - trained ,Deploy, Predict
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And I fetch the model by the name "test-model"
    And I add metrics to the model
    Then I list model metrics and expect to "1"
    And I validate model metrics equal to context.model_metrics
    When I "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When I "evaluate" the model
    Then service metadata has a model id and operation "evaluate"
    Then model status should be "deployed" with execution "True" that has function "evaluate_model"
    And Dataset has a scores file
    When I call the precision recall api
    Then I should get a json response
    Then Log "model prediction" is in model.log() with operation "evaluate"
    And I clean the project

  @DAT-79936
  Scenario: Model Management flow - Clone Model and Evaluate
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And I fetch the model by the name "test-model"
    When I "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When I "evaluate" the model
    Then model status should be "deployed" with execution "True" that has function "evaluate_model"
    Then model metadata should include operation "evaluate" with filed "datasets" and length "1"
    When I clone a model and set status "trained"
    Then model input should be equal "image", and output should be equal "box"
    Then model do not have operation "evaluate"
    When I "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    And I clean the project

  @DAT-79937
  Scenario: Model Management flow - Trigger model created , updated
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    Given I create pipeline from json in path "pipelines_json/model_trigger.json"
    When I install pipeline in context
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "created" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And I fetch the model by the name "test-model"
    Then Pipeline has "1" cycle executions
    # Pause the pipeline to pause the triggers
    When I pause pipeline in context
    And I clone a model
    # Resume the pipeline to use trigger model updated
    And I install pipeline in context
    When I update model
    Then Pipeline has "2" cycle executions
    And I clean the project