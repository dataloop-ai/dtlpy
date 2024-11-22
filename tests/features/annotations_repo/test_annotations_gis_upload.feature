Feature: Annotations repository Upload gis testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "annotations_upload"
    And I create a dataset with a random name

  @DAT-80650
  Scenario: GIS item - Upload annotations from file
    Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
    And Item in path "gis/gis.json" is uploaded to "Dataset"
    When I upload annotations from file: "gis/gisann.json" with merge "False"
    Then Item should have annotations uploaded

  @DAT-80650
  Scenario: GIS item - Upload a single annotation
    Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
    And gis item in path "gis/gis.json" is uploaded to "Dataset"
    When I add a gis annotations to item
    Then Item should have all gis annotation types uploaded

  @DAT-80996
  Scenario: GIS item - Download item annotations should work
    Given Labels in file: "assets_split/annotations_upload/labels.json" are uploaded to test Dataset
    And gis item in path "gis/gis.json" is uploaded to "Dataset"
    When I add a gis annotations to item
    Then Item should have all gis annotation types uploaded
    Given There are no files in folder "downloaded_annotations"
    When I download items annotations with "json" to "downloaded_annotations/json.json"
    Then Validate annotation file has "4" annotations



