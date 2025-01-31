Feature: Annotations adding multiple frames

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "Project_annotations_format_json"
    And I create a dataset by the name of "Dataset_annotations_format_json" in the project
    And I upload an item of type "webm video" to the dataset
    When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

  @testrail-C4533707
  @DAT-46419
  Scenario: Annotations with the same object_id wont get overwritten
    When   I upload "5" annotation with the same object id
    Then   I check that I got "5" keyframes

  @DAT-45661
  Scenario: frame attribute update
    When   I upload "5" annotation with the same object id
    When I update the "11" frame attribute of the annotation
    Then   I the only frame "11" attribute is updated
