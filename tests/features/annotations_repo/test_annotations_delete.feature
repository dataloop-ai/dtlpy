Feature: Annotaions repository Delete service testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotations_delete"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When I add "free_text" attribute to ontology
            | key=2 | title=attr2 | scope=all |

    @testrail-C4523032
    @DAT-46422
    Scenario: Delete annotation
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        And There is annotation x
        When I delete a annotation x
        Then Annotation x does not exist in item

    @testrail-C4523032
    @DAT-46422
    Scenario: Delete a non-existing Annotation
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_crud/0162_annotations.json"
        When I try to delete a non-existing annotation
        Then "NotFound" exception should be raised
        And No annotation was deleted

    @testrail-C4523032
    @DAT-46422
    Scenario: Delete Annotation using filters on Dataset level
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And Item in path "artifacts_repo/artifact_item.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And I count other Annotation except "box" using "dataset" entity
        When I delete annotation from type "box" using "dataset" entity
        Then I verify that I has the right number of annotations

    @testrail-C4523032
    @DAT-46422
    Scenario: Delete Annotation using filters on Item level
        Given Labels in file: "assets_split/annotations_crud/labels.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_crud/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And Item in path "artifacts_repo/artifact_item.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And I count other Annotation except "box" using "item" entity
        When I delete annotation from type "box" using "item" entity
        Then I verify that I has the right number of annotations
