Feature: DPK Pipeline template testing

  Background: Initiate Platform Interface and create a pipeline
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "update_dpk"


  @pipelines.delete
  @DAT-81804
  Scenario: publish two dpks with same pipeline name
    Given I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    Given I create a dataset named "Upload-data2"
    And I Add dataset to context.datasets
    When I fetch the dpk from 'apps/dpk_with_template_pipe.json' file
    And I publish a dpk to the platform
    When I install the app without custom_installation
    When I fetch the dpk from 'apps/dpk_with_template_pipe_two_datasets.json' file
    And I publish a dpk to the platform
    And I install the app without custom_installation
