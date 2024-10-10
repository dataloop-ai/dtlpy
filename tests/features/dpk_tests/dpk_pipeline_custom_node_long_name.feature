Feature: publish a dpk with pipeline Custom Node

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "dpk-long-name"

  @DAT-78090
  Scenario: Install dpk with long name - Service name should be valid
    Given I fetch the dpk from 'apps/dpk_pipeline_node_long_name.json' file
    When I publish a dpk to the platform
    And I install the app
    And I wait "5"
    Given I create pipeline from json in path "pipelines_json/pipeline_long_name_custom_name.json"
    And I install pipeline in context
    When I wait "5"
    And I get service by name "imdb-crawler-6b413285-a984-421f-96"
    Then I receive a Service entity