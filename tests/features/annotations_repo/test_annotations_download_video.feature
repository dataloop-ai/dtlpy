Feature: Annotaions repository download service testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "Project_annotations_download"
    And I create a dataset with a random name

  @testrail-C4532194
  Scenario: Download item annotations with mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/video_test.mp4" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "mask" to "downloaded_annotations/mask.mp4"
    Then video Item annotation "mask" has been downloaded to "downloaded_annotations"

  @testrail-C4532194
  Scenario: Download item annotations with instance
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/video_test.mp4" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "instance" to "downloaded_annotations/instance.mp4"
    Then video Item annotation "instance" has been downloaded to "downloaded_annotations"

  @testrail-C4532194
  Scenario: Download item annotations with json
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/video_test.mp4" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "json" to "downloaded_annotations/json.json"
    Then video Item annotation "json" has been downloaded to "downloaded_annotations"


  @testrail-C4532194
  Scenario: Download item annotations with img_mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/video_test.mp4" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "img_mask" to "downloaded_annotations/img_mask.mp4"
    Then video Item annotation "img_mask" has been downloaded to "downloaded_annotations"