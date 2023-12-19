@bot.create
Feature: Service entity Highmem Machine types

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "service-highmem-machine-types"
    And I create a dataset with a random name
    And There is a package (pushed from "services/item") by the name of "services-item"
    And I upload item in path "0000000162.jpg" to dataset


  @services.delete
  @packages.delete
  @DAT-57091
  Scenario: Create Service with pod type - highmem-xs
    When I create a service
      | service_name=services-items | package=services-items | revision=None | config=None | runtime=None | pod_type=highmem-xs |
    Then I execute the service
    And Execution was executed and finished with status "success"

  @services.delete
  @packages.delete
  @DAT-57092
  Scenario: Create Service with pod type - highmem-s
    When I create a service
      | service_name=services-items | package=services-items | revision=None | config=None | runtime=None | pod_type=highmem-s |
    Then I execute the service
    And Execution was executed and finished with status "success"
