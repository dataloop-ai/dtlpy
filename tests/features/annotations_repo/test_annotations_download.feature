Feature: Annotaions repository download service testing

  Background: Initiate Platform Interface
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "Project_annotations_download"
    And I create a dataset with a random name
    When I add "free_text" attribute to ontology
      | key=1 | title=attr1 | scope=all |
    When I add "free_text" attribute to ontology
      | key=2 | title=attr2 | scope=all |

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "mask" to "downloaded_annotations/mask.png"
    Then Item annotation "mask" has been downloaded to "downloaded_annotations"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with instance
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "instance" to "downloaded_annotations/instance.png"
    Then Item annotation "instance" has been downloaded to "downloaded_annotations"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with json
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "json" to "downloaded_annotations/json.json"
    Then Item annotation "json" has been downloaded to "downloaded_annotations"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with default
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "default" to "downloaded_annotations/json.json"
    Then Item annotation "json" has been downloaded to "downloaded_annotations"


  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with img_mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "img_mask" to "downloaded_annotations/img_mask.png"
    Then Item annotation "img_mask" has been downloaded to "downloaded_annotations"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with vtt
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download items annotations with "vtt" to "downloaded_annotations/vtt.vtt"
    Then Item annotation "vtt" has been downloaded to "downloaded_annotations"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with No specific ViewAnnotationOptions
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    Then I download the items annotations with ViewAnnotationOptions "None" enum to find "Unknown annotation download option"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with JSON ViewAnnotationsOptions
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    Then I download the items annotations with ViewAnnotationOptions "JSON" enum to find "downloaded_annotations/json/0000000162.json"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with VVT ViewAnnotationOptions
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    Then I download the items annotations with ViewAnnotationOptions "VTT" enum to find "downloaded_annotations/vvt/0000000162.vtt"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download item annotations with MASK ViewAnnotationOptions
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    Then I download the items annotations with ViewAnnotationOptions "MASK" enum to find "downloaded_annotations/mask/0000000162.png"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download annotation by id
    Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
    And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
    And There is annotation x
    And There are no files in folder "downloaded_annotations"
    When I get the annotation by id
    Then I download the annotation to "downloaded_annotations/annotation/annotation.png" with "mask" type
    And annotation file exist in the path "downloaded_annotations/annotation"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download annotation by id VTT
    Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
    And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
    And There is annotation x
    And There are no files in folder "downloaded_annotations"
    When I get the annotation by id
    Then I download the annotation to "downloaded_annotations/annotation/annotation.vtt" with "vtt" type
    And annotation file exist in the path "downloaded_annotations/annotation"

  @testrail-C4523033
  @DAT-46423
  Scenario: Download video annotation by id
    Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/ann_json_to_object/sample_video.mp4" is uploaded to "Dataset"
    And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
    And There is annotation x
    And There are no files in folder "downloaded_annotations"
    When I get the annotation by id
    Then I download the annotation to "downloaded_annotations/annotation/annotation.mp4" with "mask" type
    And annotation file exist in the path "downloaded_annotations/annotation"


  @testrail-C4523033
  @DAT-46423
  Scenario: Download dataset annotations with img_mask
    Given Labels in file: "assets_split/annotations_download/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_download/0000000162.jpg" is uploaded to "Dataset"
    And There are no files in folder "downloaded_annotations"
    And Item is annotated with annotations in file: "assets_split/annotations_download/0162_annotations.json"
    When I download dataset annotations with "img_mask" to "downloaded_annotations/img_mask.png"
    Then dataset "img_mask" folder has been downloaded to "downloaded_annotations"

  @DAT-47547
  Scenario: Download annotation by id - with out file type
    Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
    And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
    And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
    And There is annotation x
    And There are no files in folder "downloaded_annotations"
    When I get the annotation by id
    Then I download the annotation to "downloaded_annotations/annotation" with "mask" type
    And annotation file exist in the path "downloaded_annotations/annotation"
