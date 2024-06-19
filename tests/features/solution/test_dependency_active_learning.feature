@rc_only
Feature: DPK with dependencies

  Background: Login to the platform and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "active_learning_dependencies"

  @DAT-69442
  Scenario: E2E active learning using dependencies
    Given I fetch dpk active learning pipeline template from file with params
      | key          | value                                   |
      | file_name    | apps/active_learning_template_pipe.json |
      | package_name | ac-lr-package                           |
      | entry_point  | main.py                                 |
      | model_name   | ac-lr-model                             |
      | status       | trained                                 |
      | index        | 0                                       |
    When I add dependency to the dpk with params
      | key       | value           |
      | name      | active-learning |
      | mandatory | True            |
    And I publish a dpk to the platform
    Given I fetch the dpk from 'apps/dependencies/solution_default.json' file
    When I add dependency to the dpk with params
      | key       | value                          |
      | name      | context.published_dpks[0].name |
      | mandatory | True                           |
    When I add dependency to the dpk with params
      | key        | value                                            |
      | name       | yolov8                                           |
      | components | {"models":[{"name":"yolov8","mandatory": True}]} |
    And I add dependency to the dpk with params
      | key       | value                |
      | name      | hf-furniture-dataset |
      | mandatory | True                 |
    And I publish a dpk to the platform
    When I install the app
    Then I validate app dependencies are installed
    And I validate app dependencies have "usedBy" relation refs

