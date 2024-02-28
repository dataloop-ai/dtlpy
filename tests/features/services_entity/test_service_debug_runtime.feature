@bot.create
Feature: Service entity debug mode

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service-debug"
    And There is a package (pushed from "services/items") by the name of "services-debug"


  @services.delete
  @packages.delete
  @DAT-54523
  Scenario: Update service to debug mode and using custom docker- Should return <html> in response and executions should success
    Given I create a dataset with a random name
    And There are "5" items
    When I create a service
      | service_name=services-debug | package=services-debug | revision=None | config=None | runtime={"runnerImage": "python:3.10"} |
    And I send "post" gen_request with "debug_p" params
    And I send "post" gen_request with "debug_a" params
    Then I validate service has "1" instance up
    And I validate gen_request "get" with "debug_check" params and interval: "30" tries: "20" response "true"
    Then I call service.execute() on items in dataset
    When I send "post" gen_request with "terminate" params
    Then Execution was executed and finished with status "success"