Feature: Ontology Entity attributes testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "annotation_attributes"
    And I create a dataset with a random name
    And Dataset has ontology
    And Classes in file: "classes_new.json" are uploaded to test Dataset

  @DAT-69516
  Scenario: Add attributes to annotations
    When I add "yes_no" attribute to ontology
      | key=4 | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I add annotation with attrs "4" "true" to item using add annotation method
    And I upload annotation created
    Then Item in host has annotation added
    Then I validate annotation has attribute "4" with value "true"

  @DAT-71099
  Scenario: Update attributes in annotations
    When I add "yes_no" attribute to ontology
      | key=4 | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I add annotation with attrs "4" "true" to item using add annotation method
    And I upload annotation created
    And I update annotation attributes with params
      | key | value |
      | 4   | false |
    Then Item in host has annotation added
    Then I validate annotation has attribute "4" with value "false"

  @DAT-71100
  Scenario: Remove attributes from annotations
    When I add "yes_no" attribute to ontology
      | key=4 | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I add annotation with attrs "4" "true" to item using add annotation method
    And I upload annotation created
    And I update annotation attributes to empty dict
    Then Item in host has annotation added
    Then I validate annotation has no attributes


  @DAT-85316
  Scenario: Add attributes to annotations
    When I add "yes_no" attribute to ontology
      | key=4 | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I add annotation with attrs "4" "true" to item using add annotation method
    And I upload annotation created
    And I add annotation to item using add annotation method
    And I add annotation to item using add annotation method with empty dict attrs
    Then I validate annotation has all expected attributes

  @skip_test
  @DAT-94137
  @DM-cache
  Scenario: Update attributes in annotations with cache
    When I add "yes_no" attribute to ontology
      | key=4 | title=test4 | scope=all |
    Then I validate attribute "yes_no" added to ontology
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I add annotation with attrs "4" "true" to item using add annotation method
    And I upload annotation created
    And I update annotation attributes with params
      | key | value |
      | 4   | false |
    Then Item in host has annotation added
    Then I validate annotation has attribute "4" with value "false"
    And I wait "1"
    Then Item in host has annotation added
    Then I validate annotation has attribute "4" with value "false"