Feature: Items repository download annotations testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And There is a project by the name of "Project_item_annotations_download"
    And I create a dataset with a random name

  Scenario: Download item annotations with mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations from item with "mask" to "downloaded_annotations/mask.jpg"
    Then Item annotation "mask" has been downloaded to "downloaded_annotations/mask"

  Scenario: Download item annotations with instance
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations from item with "instance" to "downloaded_annotations/instance.jpg"
    Then Item annotation "instance" has been downloaded to "downloaded_annotations/instance"

  Scenario: Download item annotations with json
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations from item with "json" to "downloaded_annotations/json.jpg"
    Then Item annotation "json" has been downloaded to "downloaded_annotations/json"

  Scenario: Download item annotations with img_mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations from item with "img_mask" to "downloaded_annotations/img_mask.jpg"
    Then Item annotation "img_mask" has been downloaded to "downloaded_annotations/img_mask"

  Scenario: Download item annotations with vtt
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations from item with "vtt" to "downloaded_annotations/vtt.jpg"
    Then Item annotation "vtt" has been downloaded to "downloaded_annotations/vtt"
