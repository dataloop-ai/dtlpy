Feature: Annotation Entity Draw annotation

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "Project_test_annotation_draw"
        And I create a dataset by the name of "Dataset"
    
    Scenario: Draw - mask
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Dataset ontology has attributes "attr1" and "attr2"
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        When Item is annotated with annotations in file: "annotations_new.json"
        And I draw to image in "0000000162.jpg" all annotations with param "mask"
        Then Annotations drawn equal numpy in "draw_image_mask_should_be.npy"

    #TODO - not implemented yet
    # Scenario: Draw - instance
    #     Given Classes in file: "classes_new.json" are uploaded to test Dataset
    #     And Dataset ontology has attributes "attr1" and "attr2"
    #     And Item in path "0000000162.jpg" is uploaded to "Dataset"
    #     When Item is annotated with annotations in file: "annotations_new.json"
    #     And I draw to image in "0000000162.jpg" all annotations with param "instance"
    #     Then Annotations drawn equal numpy in "draw_image_instance_should_be.npy"

    Scenario: Finally
        Given Clean up