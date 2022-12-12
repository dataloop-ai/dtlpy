Feature: Annotations format mask

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_annotations_format_mask"
        And I create a dataset by the name of "Dataset_annotations_format_mask" in the project

    @testrail-C4532883
    Scenario: Check all mask download options - image item
        Given I upload an item of type "png image" to the dataset
        And   I upload "box" annotation to the image item
        And   I create the dir path "annotations_format_mask1"
        And   I create the dir path "annotations_format_mask2"
        Then  I delete content in path path "annotations_format_mask1"
        And   I delete content in path path "annotations_format_mask2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                       |
             | filepath           | annotations_format_mask1/png_image_item.png |
             | annotation_format  | MASK                                        |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_mask2 |
             | annotation_format  | MASK                     |
        Then  I compare between the dirs
             | Parameter | Value                    |
             | dir1      | annotations_format_mask1 |
             | dir2      | annotations_format_mask2 |

    @testrail-C4532883
    Scenario: Check all mask download options - video item
        Given I upload an item of type "mp4 video" to the dataset
        And   I upload "box" annotation to the video item
        And   I create the dir path "annotations_format_mask1"
        And   I create the dir path "annotations_format_mask2"
        Then  I delete content in path path "annotations_format_mask1"
        And   I delete content in path path "annotations_format_mask2"
        When  I call Annotation.download() using the given params
             | Parameter          | Value                                       |
             | filepath           | annotations_format_mask1/mp4_video_item.mp4 |
             | annotation_format  | MASK                                        |
        And  I call Item.annotations.download() using the given params
             | Parameter          | Value                    |
             | filepath           | annotations_format_mask2 |
             | annotation_format  | MASK                     |
        Then  I compare between the dirs
             | Parameter | Value                    |
             | dir1      | annotations_format_mask1 |
             | dir2      | annotations_format_mask2 |
