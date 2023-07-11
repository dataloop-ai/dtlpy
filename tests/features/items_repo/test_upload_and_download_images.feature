Feature: Upload and Download Images

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "delete_images_upload_download"
        And I create a dataset with a random name

    @testrail-C4529127
    @DAT-46543
    Scenario: Upload and Download Images PNG
        Given There are no items
        And I get "10" images of type "png"
        When I upload all the images
        And I download all the images
        Then The images werent changed

    @testrail-C4529127
    @DAT-46543
    Scenario: Upload and Download Images JPG
        Given There are no items
        And I get "10" images of type "jpg"
        When I upload all the images
        And I download all the images
        Then The images werent changed

    @testrail-C4529127
    @DAT-46543
    Scenario: Upload and Download Images BMP
        Given There are no items
        And I get "10" images of type "bmp"
        When I upload all the images
        And I download all the images
        Then The images werent changed

    @testrail-C4529127
    @DAT-46543
    Scenario: Download item with Overwrite True
        Given There are no items
        And I get "1" images of type "png"
        When I upload all the images
        And I overwrite "1" images of type "png"
        And I download the item with Overwrite "True"
        Then The images will be "overwritten"

    @testrail-C4529127
    @DAT-46543
    Scenario: Download item with Overwrite False
        Given There are no items
        And I get "1" images of type "png"
        When I upload all the images
        And I overwrite "1" images of type "png"
        And I download the item with Overwrite "False"
        Then The images will be "not overwritten"
