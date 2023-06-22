Feature: Bots repository get service testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    Given I create a project by the name of "bot_delete"

  @testrail-C4523062
  Scenario: Delete bot by email
    When I create a bot by the name of "some_bot"
    And I delete the created bot by "email"
    And I list bots in project
    Then I receive a bots list of "0"

  @testrail-C4523062
  Scenario: Delete bot by id
    When I create a bot by the name of "some_bot"
    And I delete the created bot by "id"
    And I list bots in project
    Then I receive a bots list of "0"

  @testrail-C4523062
  Scenario: Delete a non-existing bot
    When I try to delete a bot by the name of "Some Bot Name"
    Then "NotFound" exception should be raised

  @testrail-C4523062
  @services.delete
  @packages.delete
  @bot.create
  @DAT-48753
  Scenario: Delete a bot with active service should failed
    Given There is a package (pushed from "services/item") by the name of "services-create"
    When I create a bot by the name of "bot_service"
    And I create a service
      | service_name=services-create | package=services-create | revision=None | config=None | runtime=None | bot_user=bot_service |
    When I try to delete a bot by id
    Then "BadRequest" exception should be raised

  @testrail-C4523062
  @services.delete
  @packages.delete
  @bot.create
  @DAT-48753
  Scenario: Delete a bot from members endpoint with active service should failed
    Given There is a package (pushed from "services/item") by the name of "services-create"
    When I create a bot by the name of "bot_service_1"
    And I create a service
      | service_name=services-create | package=services-create | revision=None | config=None | runtime=None | bot_user=bot_service_1 |
    When I try to delete a member by email
    Then "BadRequest" exception should be raised