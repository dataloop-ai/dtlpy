@ATP @AIRGAPPED @ATPNONMODEL
Feature: Data Management Flow Testing

  Background: Initiate Platform Interface and create a projects and datasets
    Given Platform Interface is initialized as dlp and Environment is set according to git branch


  @DAT-79911
  Scenario: Data Management flow
    Given I create a project by the name of "Project_test_annotation_flow"
    #add roles to organization
    When I get organization
    When I add "oa-test-2@dataloop.ai" as "owner" to organization
    Then I validate "oa-test-2@dataloop.ai" is a "owner" in organization
    When I remove "oa-test-2@dataloop.ai" from organization
    When I add "oa-test-2@dataloop.ai" as "admin" to organization
    Then I validate "oa-test-2@dataloop.ai" is a "admin" in organization
    When I remove "oa-test-2@dataloop.ai" from organization
    When I add "oa-test-2@dataloop.ai" as "member" to organization
    Then I validate "oa-test-2@dataloop.ai" is a "member" in organization
    When I remove "oa-test-2@dataloop.ai" from organization
    When I add "oa-test-2@dataloop.ai" as "worker" to organization
    Then I validate "oa-test-2@dataloop.ai" is a "worker" in organization
    When I remove "oa-test-2@dataloop.ai" from organization

    And I create a dataset with a random name
    And There are "10" items
    When I create another dataset with a random name
    # clone dataset
    And Clone Dataset "clone-dataset"
    Then Cloned dataset has "10" items
    When I upload item in "0000000162.jpg" to dataset
    # merge datasets
    Then Merge Datasets "merge-dataset"
    And "merge-dataset" has "11" items
    # rename dataset
    Given I create a dataset by the name of "Original_Dataset_Name"
    When I update dataset name to "New_Dataset_Name"
    Then I create a dataset by the name of "New_Dataset_Name" in host
    And There is no dataset by the name of "Original_Dataset_Name" in host
    And The dataset from host by the name of "New_Dataset_Name" is equal to the one created
    # building queries
    Given There are items, path = "filters/image.jpg"
      | directory={"/": 3, "/dir1/": 3, "/dir1/dir2/": 3} | annotated_label={"dog": 3, "cat": 3} | annotated_type={"box": 3, "polygon": 3} | name={"dog":3, "cat":3} | metadata={"user.good": 3, "user.bad": 3, "spe-cial.ke_ys": 3} |
    When I create filters
    And I add field "dir" with values "/dir1" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "filename" with values "/dir1/dir2/*" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I list items with filters
    Then I receive "12" items

    When I create filters
    And I add field "annotated" with values "False" and operator "None"
    And I list items with filters
    Then I receive "24" items

    When I create filters
    And I add field "name" with values "*cat*" and operator "None"
    And I list items with filters
    Then I receive "6" items

    When I create filters
    And I add field "metadata.user.bad" with values "True" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "metadata.spe-cial.ke_ys" with values "False" and operator "exists"
    And I list items with filters
    Then I receive "33" items

     When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I join field "type" with values "segment" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "filename" with values "/**" and operator "None"
    And I join field "type" with values "box" and operator "ne"
    And I list items with filters
    Then I receive "9" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I join field "label" with values "dog" and operator "ne"
    And I list items with filters
    Then I receive "9" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*label*" and operator "None"
    And I list items with filters
    Then I receive "6" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*type*" and operator "None"
    And I list items with filters
    Then I receive "6" items
    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*label*" and operator "None"
    And I join field "label" with values "dog" and operator "ne"
    And I join field "type" with values "point" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*label*" and operator "None"
    And I join field "label" with values "cat" and operator "ne"
    And I join field "type" with values "point" and operator "None"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I join field "type" with values "point" and operator "None"
    And I join field "label" with values "dog" and operator "ne"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I join field "type" with values "point" and operator "None"
    And I join field "label" with values "cat" and operator "ne"
    And I list items with filters
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*label*" and operator "None"
    And I join field "label" with values "dog" and operator "ne"
    And I join field "type" with values "point" and operator "None"
    And I list items with filters
    Then I receive "3" items
    When I update items with filters, field "updated"
    And I create filters
    And I add field "metadata.user.updated" with values "True" and operator "None"
    Then I receive "3" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I list items with filters
    Then I receive "12" items
    When I update items with filters, field "annotated"
    And I create filters
    And I add field "metadata.user.annotated" with values "True" and operator "None"
    Then I receive "12" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I add field "filename" with values "/**" and operator "None"
    And I add field "name" with values "*label*" and operator "None"
    And I join field "label" with values "dog" and operator "ne"
    And I join field "type" with values "point" and operator "None"
    And I list items with filters
    Then I receive "3" items
    When I delete items with filters
    And I list items with filters
    Then I receive "0" items
    When I create filters
    And I list items with filters
    Then I receive "33" items

    When I create filters
    And I add field "annotated" with values "True" and operator "None"
    And I list items with filters
    Then I receive "9" items
    When I delete items with filters
    And I create filters
    And I list items with filters
    Then I receive "24" items

    # add un-indexed metadata
    Given I create a dataset with a random name
    Given I upload item in "0000000162.jpg" to dataset
    Given I add "QA" field to be "True" in item metadata
    When I create filters
    And I list items with filters
    Then I receive "1" items