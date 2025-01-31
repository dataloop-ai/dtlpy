Feature: Annotations repository show method testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "annotations_show"
        And I create a dataset with a random name

    @testrail-C4523038
    @DAT-46432
    Scenario: Show mask
        Given Classes in file: "assets_split/annotations_show/classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_show/0000000162.jpg" is uploaded to "Dataset"
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And I show items annotations with param "mask"
        Then I receive annotations mask and it is equal to mask in "new_mask_should_be.npy"

    @testrail-C4523038
    @DAT-46432
    Scenario: Show instance
        Given Classes in file: "assets_split/annotations_show/classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotations_show/0000000162.jpg" is uploaded to "Dataset"
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And I show items annotations with param "instance"
        Then I receive annotations mask and it is equal to mask in "new_instance_should_be.npy"

    @testrail-C4523038
    @DAT-46432
    Scenario: Show object id
        Given Classes in file: "assets_split/annotations_show/classes_new.json" are uploaded to test Dataset
        And Dataset ontology has attributes "attr1" and "attr2"
        And Item in path "assets_split/annotations_show/0000000162.jpg" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "assets_split/annotations_show/annotations_new.json"
        And Every annotation has an object id
        And I show items annotations with param "object_id"
        Then I receive annotations mask and it is equal to mask in "new_object_id_should_be.npy"


