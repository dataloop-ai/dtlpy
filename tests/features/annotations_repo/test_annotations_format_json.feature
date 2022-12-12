Feature: Annotations format json

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_format_json"
        And I create a dataset by the name of "Dataset_annotations_format_json" in the project

    @testrail-C4532882
    Scenario: Check default download is json
        Given I upload an item of type "png image" to the dataset
        And   I upload "box" annotation to the image item
        And   I create the dir path "annotations_format_json"
        When  I call Annotation.download() using the given params
             | Parameter | Value                                    |
             | filepath  | annotations_format_json/annotations.json |
        Then  I delete content in path path "annotations_format_json"


    @testrail-C4532882
    Scenario: Check all json download options - image item
        Given I upload an item of type "png image" to the dataset
        And   I upload "box" annotation to the image item
        And   I create the dir path "annotations_format_json1"
        And   I create the dir path "annotations_format_json2"
        Then  I delete content in path path "annotations_format_json1"
        And   I delete content in path path "annotations_format_json2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                        |
             | filepath           | annotations_format_json1/png_image_item.json |
             | annotation_format  | JSON                                         |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_json2 |
             | annotation_format  | JSON                     |
        Then  I compare json annotations between the files in dirs
             | Parameter           | Value                    |
             | annotation_json_dir | annotations_format_json1 |
             | item_json_dir       | annotations_format_json2 |

    @testrail-C4532882
    Scenario: Check all json download options - video item
        Given I upload an item of type "webm video" to the dataset
        And   I upload "box" annotation to the video item
        And   I create the dir path "annotations_format_json1"
        And   I create the dir path "annotations_format_json2"
        Then  I delete content in path path "annotations_format_json1"
        And   I delete content in path path "annotations_format_json2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                         |
             | filepath           | annotations_format_json1/webm_video_item.json |
             | annotation_format  | JSON                                          |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_json2 |
             | annotation_format  | JSON                     |
        Then  I compare json annotations between the files in dirs
             | Parameter           | Value                    |
             | annotation_json_dir | annotations_format_json1 |
             | item_json_dir       | annotations_format_json2 |

    @testrail-C4532882
    Scenario: Check all json download options - audio item
        Given I upload an item of type "mp3 audio" to the dataset
        And   I upload "subtitle" annotation to the audio item
        And   I create the dir path "annotations_format_json1"
        And   I create the dir path "annotations_format_json2"
        Then  I delete content in path path "annotations_format_json1"
        And   I delete content in path path "annotations_format_json2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                        |
             | filepath           | annotations_format_json1/mp3_audio_item.json |
             | annotation_format  | JSON                                         |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_json2 |
             | annotation_format  | JSON                     |
        Then  I compare json annotations between the files in dirs
             | Parameter           | Value                    |
             | annotation_json_dir | annotations_format_json1 |
             | item_json_dir       | annotations_format_json2 |

    @testrail-C4532882
    Scenario: Check all json download options - text item
        Given I upload an item of type "txt text" to the dataset
        And   I upload "text mark" annotation to the text item
        And   I create the dir path "annotations_format_json1"
        And   I create the dir path "annotations_format_json2"
        Then  I delete content in path path "annotations_format_json1"
        And   I delete content in path path "annotations_format_json2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                        |
             | filepath           | annotations_format_json1/txt_text_item.json |
             | annotation_format  | JSON                                         |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_json2 |
             | annotation_format  | JSON                     |
        Then  I compare json annotations between the files in dirs
             | Parameter           | Value                    |
             | annotation_json_dir | annotations_format_json1 |
             | item_json_dir       | annotations_format_json2 |