@ATP @AIRGAPPED @ATPNONMODEL
Feature: Annotation Flow Testing

  Background: Initiate Platform Interface and create a projects and datasets
    Given Platform Interface is initialized as dlp and Environment is set according to git branch


  @DAT-79639
  Scenario: Annotation flow
    Given I create a project by the name of "Project_test_annotation_flow"
    And I create a dataset with a random name
    And Item in path "0000000162.jpg" is uploaded to "Dataset"
    # add item description
    When  I Add description "Item description" to item
    Then  I validate item.description has "Item description" value
    # create recipe with labels and add attribute
    When I create a new ontology with labels from file "labels.json"
    And I update dataset ontology to the one created
    And I add "checkbox" attribute to ontology
      | key=1 | title=test1 | values=['a','b','c'] |
    # add labeling instructions to recipe
    Then Add instruction "sample.pdf" to Recipe
    And instruction are exist
    # upload annotations
    Given I upload "box" annotation to the image item
    And I upload "polygon" annotation to the image item
    And I upload "semantic segmentation" annotation to the image item
    And I upload "classification" annotation to the image item
    And I upload "rotated box" annotation to the image item
    And I upload "cube" annotation to the image item
    And I upload "polyline" annotation to the image item
    And I upload "ellipse" annotation to the image item
    And I upload "point" annotation to the image item
    And I upload "note" annotation to the image item
    When I list all item entity annotations
    Then I validate that I have "9" annotations in item
    # set objectId
    When I set object id for annotation "3" to be "1"
    Then I validate that annotation "3" has object id "1"
    # delete annotation
    When I delete annotation from type "point" using "item" entity
    Then I validate that I have "8" annotations in item
    # replace label for existing annotation
    Given I change annotation "2" value to "person"
    Then I validate that I have an annotation in item with the name "person"
    # execute mask_to_polygon
    When I execute to_polygon function on mask annotation
    Then I have "2" "segment" annotations
    # execute polygon_to_mask
    When I execute to_mask function on polygon annotation
    Then I have "2" "binary" annotations
    # export JSON annotations
    Given I create the dir path "annotations_format_json"
    When I download items annotations with "json" to "annotations_format_json/json.json"
    Then Item annotation "json" has been downloaded to "annotations_format_json"
    # export mask
    When I download items annotations from item with "img_mask" to "annotations_format_json/img_mask.jpg"
    Then Item annotation "img_mask" has been downloaded to "annotations_format_json/img_mask"
    When I download all mask annotations to "annotations_format_json/mask.png"
    Then Item annotation "mask" has been downloaded to "annotations_format_json"
    # upload JSON annotations
    When I delete all annotations in item
    When I upload annotations from file: "annotations_format_json/json.json" with merge "False"
    Then I validate that I have "8" annotations in item
    # add annotation note
    Given I upload "polyline" annotation with description "Annotation description" to the image item
    Then I validate annotation.description has "Annotation description" value
    Then I validate that I have "9" annotations in item
    # update/edit annotation
    When I update "point" annotation position on canvas
    Then I validate that the "point" annotation position was changed
    # sort annotations
    When I sort annotations by "type" in "ascending" order
    Then I validate that annotations are sorted by "type" in "ascending" order
    # add modality to item
    When I upload an item with its modalities
    Then I validate item has modalities