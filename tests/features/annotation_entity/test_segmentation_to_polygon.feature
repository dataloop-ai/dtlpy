Feature: Annotation Segmentation to polygon

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And   I create a project by the name of "segmentation_to_polygon_project"

  @testrail-C4533901
  @DAT-46448
  Scenario: Segmentation to polygon
    Given I create a dataset with a random name
    And   Item in path "0000000162.jpg" is uploaded to "Dataset"
    And   Classes in file: "classes_new.json" are uploaded to test Dataset
    And   I have a segmentation annotation
    When  I call Polygon.from_segmentation() using "1" nax_instances
    Then  The polygon will match to the json file "segmentation_to_polygon/0000000162_single.json"

  @testrail-C4533901
  @DAT-46448
  Scenario: Multi segmentation to polygons
    Given I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    And   Classes in file: "classes_new.json" are uploaded to test Dataset
    And   I have a multi segmentation annotations
    When  I call Polygon.from_segmentation() using "2" nax_instances
    Then  The polygon will match to the json file "segmentation_to_polygon/0000000162_multi.json"

