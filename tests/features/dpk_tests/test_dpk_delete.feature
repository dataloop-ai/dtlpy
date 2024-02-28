Feature: Delete dpk

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    When I create a project by the name of "delete_dpk"

  @DAT-62990
  Scenario: Creator should be able to delete dpk should
    When I fetch the dpk from 'apps/app.json' file
    And I publish a dpk to the platform
    And I delete published_dpk
    And I try get the "published_dpk" by id
    Then "NotFound" exception should be raised


  @DAT-65577
  Scenario: Delete dpk - Should delete all the dpk versions
    When I fetch the dpk from 'apps/app_include_models.json' file
    And I publish a dpk to the platform
    And I increment dpk version
    And I publish a dpk
    When I delete dpk with all revisions
    And I try get the "dpk" by id
    Then "NotFound" exception should be raised
    When I try get the "dpk" by name
    Then "NotFound" exception should be raised