@bot.create
Feature: Services repository output limit service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service_output_limit"
    And I create a dataset with a random name
    And There is a package (pushed from "services/output_limit") by the name of "services-limit"

  @services.delete
  @packages.delete
  @DAT-54723
  Scenario: Service should response failed on 4 mb output limit
    When I create a service
      | service_name=services-limit | package=services-limit | revision=None | config=None | runtime=None |
    Then I receive a Service entity
    When I execute service on "5" with type "Integer" with name "size"
    Then "The function execution was successful, but the output couldn't be saved because it was larger than the maximum size allowed of 4.0MB" in error message