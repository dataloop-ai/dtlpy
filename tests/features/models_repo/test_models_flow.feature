Feature: Models repository flow testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "model_mgmt"
    And I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item

  @DAT-48263
  @DAT-51111
  @DAT-51143
  @DAT-51144
  @DAT-51145
  Scenario: test flow model
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model form package by the name of "test-model" with status "created"
    When i "train" the model
    Then service metadata has a model id and operation "train"
    Then model status should be "trained" with execution "True" that has function "train_model"
    When i "deploy" the model
    Then model status should be "deployed" with execution "False" that has function "None"
    When i "evaluate" the model
    Then model status should be "deployed" with execution "True" that has function "evaluate_model"
    And service metadata has a model id and operation "evaluate"
    And Dataset has a scores file
    When i call the precision recall api
    Then i should get a json response
    Then Log "model training" is in model.log() with operation "train"
    Then Log "model prediction" is in model.log() with operation "evaluate"

  @DAT-50829
  Scenario: test model - failed
    When I create a dummy model package by the name of "modelfaild" with entry point "failedmain.py"
    And I create a model form package by the name of "test-model-failed" with status "created"
    When i "train" the model
    Then model status should be "failed" with execution "True" that has function "train_model"


  @DAT-52904
  Scenario: test flow model - initPrams
    When I create a dummy model package by the name of "initmodel" with entry point "main.py"
    And I create a model form package by the name of "test-model-init" with status "created"
    When i train the model with init param model none
    Then model status should be "trained" with execution "True" that has function "train_model"


  @DAT-53071
  Scenario: test evaluate service updated
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model form package by the name of "test-model-eve" with status "trained"
    And i add a Service config runtime
      | runnerImage=ImageA | podType=regular-xs |
    When i "evaluate" the model
    Then check service runtime
      | runnerImage=ImageA | podType=regular-xs |
    When i add a Service config runtime
      | runnerImage=ImageB | podType=regular-s |
    When i "evaluate" the model
    Then check service runtime
      | runnerImage=ImageB | podType=regular-s |
