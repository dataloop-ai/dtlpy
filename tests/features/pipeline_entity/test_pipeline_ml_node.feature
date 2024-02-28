@bot.create
Feature: Pipeline ml node testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "ml_node"
    And I create a dataset with a random name

  @pipelines.delete
  @DAT-54797
  Scenario: Pipeline - ml predict node updated variable
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel" with entry point "main.py"
    And I create a model from package by the name of "test-model" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model"
    Given Pipeline which have a model variable and predict ml node that reference to this model variable file "ml_predict.json"
    When I install pipeline in context
    Then i have a model service
    When I clone the model
    And i fetch the model by the name "clone_test-model"
    And I update the model variable in pipeline to reference to this model
    Then I wait "3"
    And the model service id updated

  @pipelines.delete
  @services.delete
  @DAT-55427
  Scenario: Pipeline - ml predict node updated variable with old deploy model
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "dummymodel-1" with entry point "main.py"
    And I create a model from package by the name of "test-model-1" with status "trained" in index "0"
    And I publish a dpk to the platform
    And I install the app
    And i fetch the model by the name "test-model-1"
    Given Pipeline which have a model variable and predict ml node that reference to this model variable file "ml_predict.json"
    When I install pipeline in context
    Then i have a model service
    When i "deploy" the model
    When I clone the model
    And i fetch the model by the name "clone_test-model-1"
    And I update the model variable in pipeline to reference to this model
    Then I wait "3"
    Then the model service id updated
    Then models with the names "test-model-1,test-model-2" status "deployed"