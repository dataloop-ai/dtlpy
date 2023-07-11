Feature: Contributor Roles SDK

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "contributor-project"

  @testrail-C4523096
  @DAT-46507
  Scenario: Contributor Roles SDK Scenario project owner
    When List Members
    Then Add Members "annotator1@dataloop.ai" as "owner"
    And Update Members "annotator1@dataloop.ai" to "engineer"
    And Remove Members "annotator1@dataloop.ai"

  @testrail-C4523096
  @DAT-46507
  Scenario: Contributor Roles SDK Scenario engineer
    When List Members
    Then Add Members "annotator1@dataloop.ai" as "engineer"
    And Update Members "annotator1@dataloop.ai" to "annotationManager"
    And Remove Members "annotator1@dataloop.ai"


  @testrail-C4523096
  @DAT-46507
  Scenario: Contributor Roles SDK Scenario annotation manager
    When List Members
    Then Add Members "annotator1@dataloop.ai" as "annotationManager"
    And Update Members "annotator1@dataloop.ai" to "annotator"
    And Remove Members "annotator1@dataloop.ai"

  @testrail-C4523096
  @DAT-46507
  Scenario: Contributor Roles SDK Scenario annotator
    When List Members
    Then Add Members "annotator1@dataloop.ai" as "annotator"
    And Update Members "annotator1@dataloop.ai" to "annotationManager"
    And Remove Members "annotator1@dataloop.ai"
