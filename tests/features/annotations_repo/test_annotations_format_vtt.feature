Feature: Annotations format vtt

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_format_vtt"
        And I create a dataset by the name of "Dataset_annotations_format_vtt" in the project
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |

    @testrail-C4532884
    @DAT-46429
    Scenario: Check all vtt download options
        Given I upload an item of type "mp3 audio" to the dataset
        And   I upload "subtitle" annotation to the audio item
        And   I create the dir path "annotations_format_vtt1"
        And   I create the dir path "annotations_format_vtt2"
        And   I create the dir path "annotations_format_vtt3"
        Then  I delete content in path path "annotations_format_vtt1"
        And   I delete content in path path "annotations_format_vtt2"
        And   I delete content in path path "annotations_format_vtt3"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                      |
             | filepath           | annotations_format_vtt1/mp3_audio_item.vtt |
             | annotation_format  | VTT                                        |
        And   I call Item.annotations.download() using the given params
             | Parameter          | Value                   |
             | filepath           | annotations_format_vtt2 |
             | annotation_format  | VTT                     |
        Then  I compare between the dirs
             | Parameter | Value                   |
             | dir1      | annotations_format_vtt1 |
             | dir2      | annotations_format_vtt2 |
        Given I init Filters() using the given params
             | Parameter | Value |
             | resource  | ITEM  |
        When  I call Filters.add() using the given params
             | Parameter | Value              |
             | field     | name               |
             | values    | mp3_audio_item.mp3 |
        And   I call dataset.download_annotations() using the given params
             | Parameter          | Value                   |
             | local_path         | annotations_format_vtt3 |
             | annotation_options | VTT                     |
        Then  I compare json metadata and annotationsCount between the files in dirs
             | Parameter        | Value                       |
             | item_json_dir    | annotations_format_vtt2     |
             | dataset_json_dir | annotations_format_vtt3/vtt |

