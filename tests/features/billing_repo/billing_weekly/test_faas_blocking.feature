@bot.create
Feature: plan creation

  Background: Initiate Platform Interface

    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    Given I log in as a "superuser"
    Given I create "org" name "custom_subscription"
    Given I create "project" name "custom_subscription"
    When I create "dataset" name "custom_subscription"
    When I update the project org
    When I create a bot by the name of "boty"
    Given Add Members "user" as "owner"
    Given I fetch "subscription_payload.json" file from "billing"

  @DAT-77314
  Scenario: Validate regular-xs, highmem-s, regular-m quota limit reached - with FF

    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-regular-xs=0.01 | account |
    When I delete the free subscription
    Given I fetch "enable-custom-subscription-blocking-FF.json" file from "billing"
    When I "create" enable-custom-subscription-blocking = True
    Given There is a package (pushed from "services/item") by the name of "services-log"
    When I create a service with autoscaler
      | service_name=service-xs | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-xs |
    Then I validate service has "1" instance up
    When I get analytics query "regular-xs"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message
    Given I fetch "subscription_payload.json" file from "billing"
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-highmem-s=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=highmem-s |
    Then I validate service has "1" instance up
    When I get analytics query "highmem-s"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-regular-m=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message

  @DAT-77315
  Scenario: Validate regular-xs, highmem-s, regular-m quota limit reached - without FF

    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-regular-xs=0.01 | account |
    When I delete the free subscription
    Given There is a package (pushed from "services/item") by the name of "services-log"
    When I create a service with autoscaler
      | service_name=service-xs | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-xs |
    Then I validate service has "1" instance up
    When I get analytics query "regular-xs"
    When I update quotas
    When I log in as a "user"
    Then I activate service
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-highmem-s=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=highmem-s |
    Then I validate service has "1" instance up
    When I get analytics query "highmem-s"
    When I update quotas
    When I log in as a "user"
    Then I activate service
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-regular-m=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m"
    When I update quotas
    When I log in as a "user"
    Then I activate service

