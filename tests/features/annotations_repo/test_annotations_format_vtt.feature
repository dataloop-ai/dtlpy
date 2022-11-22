Feature: Annotations format vtt

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_format_vtt"
        And I create a dataset by the name of "Dataset_annotations_format_vtt" in the project

    @testrail-C4532884
    Scenario: Check all vtt download options
        Given I upload an item of type "mp3 audio" to the dataset
        And   I upload "subtitle" annotation to the audio item
        And   I create the dir path "annotations_format_vtt1"
        And   I create the dir path "annotations_format_vtt2"
        Then  I delete content in path path "annotations_format_vtt1"
        And   I delete content in path path "annotations_format_vtt2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                       |
             | filepath           | annotations_format_vtt1/mp3_audio_item.vtt |
             | annotation_format  | VTT                                         |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                   |
             | filepath           | annotations_format_vtt2 |
             | annotation_format  | VTT                     |
        Then  I compare between the dirs
             | Parameter | Value                   |
             | dir1      | annotations_format_vtt1 |
             | dir2      | annotations_format_vtt2 |
