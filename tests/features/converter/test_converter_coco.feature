Feature: Converter coco format

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "coco_converter"
    And I create a dataset with a random name

  @testrail-C4523080
  Scenario: Convert local coco dataset to dataloop
    Given There is a local "coco" dataset in "converter/coco/local_dataset"
    When I convert local "coco" dataset to "dataloop"
    Given Local path in "converter/coco/reverse" is clean
    When I reverse dataloop dataset to local "coco" in "converter/coco/reverse"
    Then local "coco" dataset in "converter/coco/local_dataset" is equal to reversed dataset in "converter/coco/reverse"

  @testrail-C4523080
  Scenario: Convert local coco dataset with inner folders to dataloop
    Given There is a local "coco" dataset in "converter/coco/local_dataset_inner"
    When I convert local "coco" dataset to "dataloop"
    Given Local path in "converter/coco/reverse" is clean
    When I reverse dataloop dataset to local "coco" in "converter/coco/reverse"
    Then local "coco" dataset in "converter/coco/local_dataset_inner" is equal to reversed dataset in "converter/coco/reverse"

  @testrail-C4523080
  Scenario: Upload dataset with inner folder using coco converter
    Given I use "COCO" converter to upload items with annotations to the dataset using the given params
      | Parameter              | Value                                                        |
      | local_items_path       | converter/coco/local_coco_with_folders/items                 |
      | local_annotations_path | converter/coco/local_coco_with_folders/annotations/coco.json |
    And   Local path in "converter/coco/local_downloaded_items" is clean
    And   I download the dataset items annotations in "COCO" format using the given params
      | Parameter  | Value                                 |
      | local_path | converter/coco/local_downloaded_items |
    Then  I use "COCO" format to compare the uploaded annotations with the downloaded annotations

  @testrail-C4533546
  Scenario: Convert local coco dataset do not overwrite the existing labels
    Given There is a local "coco" dataset in "converter/coco/local_dataset"
    When I add single root Label "laptop"
    And I convert local "coco" dataset to "dataloop"
    Then The converter do not overwrite the existing label


  @DAT-47083
  Scenario: Convert local coco dataset to dataloop - with empty segmentation
    Given There is a local "coco" dataset in "converter/emptyseg"
    When I convert local "coco" dataset to "dataloop"
    Given Local path in "converter/emptyseg/reverse" is clean
    When I reverse dataloop dataset to local "coco" in "converter/emptyseg/reverse"
    Then local "coco" dataset in "converter/emptyseg" is equal to reversed dataset in "converter/emptyseg/reverse"