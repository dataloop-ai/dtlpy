Feature: Datasets repository download_annotations service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "datasets_download_annotations"
    And I create a dataset with a random name
    And Item in path "0000000162.png" is uploaded to "Dataset"
    When I add "free_text" attribute to ontology
      | key=1 | title=attr1 | scope=all |
    When I add "free_text" attribute to ontology
      | key=2 | title=attr2 | scope=all |

  Scenario: upload annotations
    Then I upload annotations to dataset
    And Annotations in item equal to the annotations uploaded


  Scenario: upload annotations use new end point
    When Item in path "0000000162.png" is uploaded to "Dataset" in remote path "/a/b/c"
    Then I upload annotations to dataset in new end point "/a/b/c"
    And Annotations in item equal to the annotations uploaded


