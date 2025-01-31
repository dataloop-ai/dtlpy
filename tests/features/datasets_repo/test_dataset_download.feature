Feature: Datasets repository download service testing

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "datasets_download"
    When I add "free_text" attribute to ontology
      | key=1 | title=attr1 | scope=all |
    When I add "free_text" attribute to ontology
      | key=2 | title=attr2 | scope=all |

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with items
    Given I create a dataset with a random name
    And Item in path "0000000162.png" is uploaded to "Dataset"
    And Labels in file: "labels.json" are uploaded to test Dataset
    And Item is annotated with annotations in file: "0162_annotations.json"
    And There are no folder or files in folder "downloaded_dataset"
    When I download dataset to "downloaded_dataset"
    Then Dataset downloaded to "downloaded_dataset" is equal to dataset in "downloaded_dataset-should_be"
    And There is no "log" file in folder "downloaded_dataset"

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with dot in local path
    Given I create a dataset by the name of "dot.dataset1"
    And Item in path "0000000162.png" is uploaded to "Dataset"
    And Labels in file: "labels.json" are uploaded to test Dataset
    And Item is annotated with annotations in file: "0162_annotations.json"
    And There are no folder or files in folder "downloaded.dataset"
    When I download dataset to "downloaded.dataset"
    Then Dataset downloaded to "downloaded.dataset" is equal to dataset in "downloaded_dataset-should_be"
    And There is no "log" file in folder "downloaded.dataset"

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with Overwrite True
    Given I create a dataset with a random name
    And There are no items
    And I get "1" images of type "png" for the dataset
    When I upload all the images for the dataset
    And I download the dataset without Overwrite variable
    And I modify the downloaded item
    And I download the dataset with Overwrite "True"
    Then The dataset item will be "overwritten"

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with Overwrite False
    Given I create a dataset with a random name
    And There are no items
    And I get "1" images of type "png" for the dataset
    When I upload all the images for the dataset
    And I download the dataset without Overwrite variable
    And I modify the downloaded item
    And I download the dataset with Overwrite "False"
    Then The dataset item will be "not overwritten"

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with dot in local path without item folder
    Given I create a dataset by the name of "dot.datasetnoitem"
    And Item in path "0000000162.png" is uploaded to "Dataset"
    And Labels in file: "labels.json" are uploaded to test Dataset
    And Item is annotated with annotations in file: "0162_annotations.json"
    And There are no folder or files in folder "downloaded.dataset"
    When I download dataset to "downloaded.dataset" without item folder
    Then Dataset downloaded to "downloaded.dataset" is equal to dataset in "downloaded_dataset-should_be"
    And There is no "log" file in folder "downloaded.dataset"

  @testrail-C4523092
  @DAT-46500
  Scenario: Download dataset with json items
    Given I create a dataset with a random name
    And Item in path "linked_items-should_be/items/wrong-linked-item.json" is uploaded to "Dataset"
    And There are no folder or files in folder "linked_items"
    When I download dataset to "linked_items"
    Then The folder "linked_items" is equal to to "linked_items-should_be"
    And There is no "log" file in folder "linked_items"

  @testrail-C4533352
  @DAT-46500
  Scenario: Download dataset folder
    Given I create a dataset with a random name
    And There are no items
    And I upload an item by the name of "test_item.jpg"
    And I upload item by the name of "test_item.jpg" to a remote path "test"
    And Folder "test_items_download" is empty
    When I download dataset folder "/test" to "test_items_download"
    Then There are "1" files in "test_items_download"

  @testrail-C4533352
  @DAT-46500
  Scenario: Download dataset folder with sub folder
    Given I create a dataset with a random name
    And There are no items
    And I upload an item by the name of "test_item.jpg"
    And I upload item by the name of "test_item.jpg" to a remote path "test"
    And I upload item by the name of "test_item.jpg" to a remote path "test/subfolder"
    And Folder "test_items_download" is empty
    When I download dataset folder "/test" to "test_items_download"
    Then There are "2" files in "test_items_download"
