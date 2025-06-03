Feature: Annotation Entity Add annotation

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "Project_test_annotation_add"
        And I create a dataset with a random name
        When I add "free_text" attribute to ontology
            | key=1 | title=attr1 | scope=all |
        When I add "free_text" attribute to ontology
            | key=2 | title=attr2 | scope=all |

    @testrail-C4523041
    @DAT-46437
    Scenario: Image - using add annotation method
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I upload annotation created
        Then Item in host has annotation added

    @testrail-C4523041
    @DAT-46437
    Scenario: Video - using add annotation method
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I add some frames to annotation
        And I upload annotation created
        Then Item in host has annotation added

    @testrail-C4523041
    @DAT-46437
    Scenario: Audio - using add annotation method
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "simple_audio.mp3" is uploaded to "Dataset"
        When I add annotation to audio using add annotation method
        Then audio in host has annotation added

    @DAT-56077
    Scenario: annotation color is set to default
        Given Item in path "0000000162.jpg" is uploaded to "Dataset"
        And I have a segmentation annotation
        And Classes in file: "classes_new.json" are uploaded to test Dataset
        Then annotation color is set to recipe color

    @skip_test
    @DAT-94137
    @DM-cache
    Scenario: Image - using add annotation method with cache
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "0000000162.jpg" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I upload annotation created
        Then Item in host has annotation added
        And I wait "1"
        Then Item in host has annotation added


    @skip_test
    @DAT-94137
    @DM-cache
    Scenario: Video - using add annotation method with cache
        Given Classes in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        When I add annotation to item using add annotation method
        And I add some frames to annotation
        And I upload annotation created
        Then Item in host has annotation added
        And I wait "1"
        Then Item in host has annotation added


    @skip_test
    @DAT-94137
    @DM-cache
    Scenario: Audio - using add annotation method with cache
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "simple_audio.mp3" is uploaded to "Dataset"
        When I add annotation to audio using add annotation method
        Then audio in host has annotation added
        And I wait "1"
        Then audio in host has annotation added

    @skip_test
    @DAT-94137
    @DM-cache
    Scenario: annotation color is set to default with cache
        Given Item in path "0000000162.jpg" is uploaded to "Dataset"
        And I have a segmentation annotation
        And Classes in file: "classes_new.json" are uploaded to test Dataset
        Then annotation color is set to recipe color
        And I wait "1"
        Then annotation color is set to recipe color