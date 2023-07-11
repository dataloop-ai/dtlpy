Feature: Annotations repository Draw method testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_draw"
        And I create a dataset with a random name

    @testrail-C4523034
    @DAT-46425
    Scenario: Draw mask
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Dataset ontology has attributes "attr1" and "attr2"
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "annotations_new.json"
        And I draw items annotations with param "mask" to image in "0000000162.jpg"
        Then I receive annotations mask and it is equal to mask in "draw_collection_should_be.npy"

    #TODO  - not implemented
    # Scenario: Draw instance
    #     Given Classes in file: "classes_new.json" are uploaded to test Dataset
    #     And Dataset ontology has attributes "attr1" and "attr2"
    #     And Item in path "0000000162.jpg" is uploaded to "Dataset"
    #     When Item is annotated with annotations in file: "annotations_new.json"
    #     And I draw items annotations with param "instance"
    #     Then I receive annotations mask and it is equal to mask in "new_instance_should_be_draw.npy"


