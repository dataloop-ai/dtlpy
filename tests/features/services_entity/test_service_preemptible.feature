@bot.create
Feature: Services entity preemptible attribute

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "services_preemptible"
    And I create a dataset with a random name
    And There is a package (pushed from "services/item") by the name of "services-preemptible"

  @services.delete
  @packages.delete
  @testrail-C4533503
  @DAT-46608
  Scenario: Update execution_timeout - Preemptible should updated to False
    When I create a service
      | service_name=services-preemptible | package=services-preemptible | revision=None | config=None | runtime=None | execution_timeout=360000 |
    Then I expect preemptible value to be "False"
    And Object "Service" to_json() equals to Platform json.


  @services.delete
  @packages.delete
  @testrail-C4533503
  @DAT-46608
  Scenario: Update max_attempts - Preemptible should updated to False
    When I create a service
      | service_name=services-preemptible | package=services-preemptible | revision=None | config=None | runtime=None | max_attempts=1 |
    Then I expect preemptible value to be "False"
    And Object "Service" to_json() equals to Platform json.



