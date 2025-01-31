Feature: Annotation description with builder - audio item

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And   I create a project by the name of "annotations_description_project"
        And   I create a dataset by the name of "annotations_description_dataset" in the project
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

    @testrail-C4532807
    @DAT-46439
    Scenario: Upload classification annotation with description
        Given I upload an item of type "mp3 audio" to the dataset
        And   I upload "subtitle" annotation with description "Annotation description" to the audio item
        Then  I validate annotation.description has "Annotation description" value
        When  I remove description from the annotation
        Then  I validate annotation.description has "None" value
