Feature: Integrations repository create testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "sdk_cross_integrations"
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"

  @DAT-83866
  Scenario: ECR integration Flow
      Given There are no private registry integrations in the organization
      Given A deployed service with custom docker image from ECR private registry
      And I execute the service
      Then I should get an ImagePullBackOff error
      When I create an ECR integration
      And I pause and resume the service
      Then The execution should complete successfully
      When I delete the ECR integration
      And I pause and resume the service
      Given I execute the service
      Then I should get an ImagePullBackOff error