@bot.create
Feature: plan creation

  Background: Initiate Platform Interface

    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    Given I log in as a "superuser"
    Given I create "org" name "custom_subscription_budget"
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
    When I get analytics query "regular-xs" for 120 seconds
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
    When I get analytics query "highmem-s" for 120 seconds
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
    When I get analytics query "regular-m" for 120 seconds
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
    When I get analytics query "regular-xs" for 120 seconds
    When I update quotas
    When I log in as a "user"
    Then I activate service
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-highmem-s=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=highmem-s |
    Then I validate service has "1" instance up
    When I get analytics query "highmem-s" for 120 seconds
    When I update quotas
    When I log in as a "user"
    Then I activate service
    Given I log in as a "superuser"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-cpu-regular-m=0.01 | account |
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m" for 120 seconds
    When I update quotas
    When I log in as a "user"
    Then I activate service


  @DAT-84593
  Scenario: Validate Compute Budget with multiple subscriptions

    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-budget=0.01 | account |
    When I delete the free subscription
    Given I fetch "enable-custom-subscription-blocking-FF.json" file from "billing"
    When I "create" enable-custom-subscription-blocking = True
    Given There is a package (pushed from "services/item") by the name of "services-log"
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-s |
    Then I validate service has "1" instance up
    When I get analytics query "regular-s" for 120 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message
    Given I log in as a "superuser"
    Given I fetch "subscription_payload.json" file from "billing"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-budget=0.01 | account |
    When I update quotas
    When I log in as a "user"
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m" for 60 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message

  @DAT-84594
  Scenario: Validate Compute Budget with multiple subscriptions - without FF

    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-budget=0.01 | account |
    When I delete the free subscription
    Given There is a package (pushed from "services/item") by the name of "services-log"
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-s |
    Then I validate service has "1" instance up
    When I get analytics query "regular-s" for 120 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I activate service
    Given I log in as a "superuser"
    Given I fetch "subscription_payload.json" file from "billing"
    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-budget=0.01 | account |
    When I update quotas
    When I log in as a "user"
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m" for 60 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I activate service

  @DAT-84595
  Scenario: Validate Compute Budget with few machines

    When I create custom subscription
      | annotation-tool-hours=777 | data-points=777 | api-calls=777 | hosted-storage=777 | compute-budget=0.098 | account |
    When I delete the free subscription
    Given I fetch "enable-custom-subscription-blocking-FF.json" file from "billing"
    When I "create" enable-custom-subscription-blocking = True
    Given There is a package (pushed from "services/item") by the name of "services-log"
    When I create a service with autoscaler
      | service_name=service-xs | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-xs |
    Then I validate service has "1" instance up
    When I get analytics query "regular-xs" for 120 seconds
    When I update quotas
    When I log in as a "user"
    Then I deactivate service named "service-xs"
    When I create a service with autoscaler
      | service_name=service-s | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-s |
    Then I validate service has "1" instance up
    When I get analytics query "regular-s" for 120 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I deactivate service named "service-s"
    When I create a service with autoscaler
      | service_name=service-m | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-m |
    Then I validate service has "1" instance up
    When I get analytics query "regular-m" for 120 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I deactivate service named "service-m"
    When I create a service with autoscaler
      | service_name=service-l | package=services-log-init | revision=None | config=None | runtime=None | pod_type=regular-l |
    Then I validate service has "1" instance up
    When I get analytics query "regular-l" for 120 seconds
    Given I log in as a "superuser"
    When I update quotas
    When I log in as a "user"
    Then I unable to activate service
    Then "Trial users do not have permission to create services" in error message





