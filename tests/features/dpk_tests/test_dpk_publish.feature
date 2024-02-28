Feature: publish a dpk

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "test_app_ins"


  @testrail-C4524925
  @DAT-46514
  Scenario: publishing a dpk
    Given I fetch the dpk from 'apps/app.json' file
    When I publish a dpk to the platform
    Then The user defined properties should have the same values
    And id, name, createdAt, codebase, url and creator should have values

  @DAT-65868
  Scenario: publishing a dpk with invalid dpk
    Given I fetch the dpk from 'apps/app.json' file
    When I publish without context
    Then "BadRequest" exception should be raised

  @DAT-66447
  Scenario: Publish dpk with scope public - Should get 'invalid rules'
    Given I fetch the dpk from 'apps/dpk_scope_public.json' file
    When I try to publish a dpk to the platform
    Then "Forbidden" exception should be raised