Feature: Item Move function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project1"
        And I create a dataset with a random name
        And Item in path "0000000162.jpg" is uploaded to "Dataset"


    @testrail-C4523122
    Scenario: Move file to new directory with / in the end without dot
        When  I move the item to "/new_dir/"
        Then  I insure that new full name is "/new_dir/0000000162.jpg"


    @testrail-C4523122
    Scenario: Move file to new directory with / in the end with dot
        When  I move the item to "/new_dir.1/"
        Then  I insure that new full name is "/new_dir.1/0000000162.jpg"


    @testrail-C4523122
    Scenario: Move file to new directory with / in the end t an existing directory
        Given I have directory with the name "/new_dir"
        When  I move the item to "/new_dir/"
        Then  I insure that new full name is "/new_dir/0000000162.jpg"


    @testrail-C4523122
    Scenario: Move file to new directory without / in the end and with dot in the path
        Given I have directory with the name "/new_dir.1"
        When  I move the item to "/new_dir.1"
        Then  I insure that new full name is "/new_dir.1/0000000162.jpg"


    @testrail-C4523122
    Scenario: Move file to new directory without / in the end  and without dot in the path
        Given I have directory with the name "/new_dir"
        When  I move the item to "/new_dir"
        Then  I insure that new full name is "/new_dir/0000000162.jpg"


    @testrail-C4523122
    Scenario: Move file to new non existing directory  without dot
        When  I move the item to "/new_dir"
        Then  I insure that new full name is "/new_dir"


    @testrail-C4523122
    Scenario: Move file to new  non existing directory  with dot
        When  I move the item to "/pic.jpg"
        Then  I insure that new full name is "/pic.jpg"


    @testrail-C4523122
    Scenario: Move file to new directory without adding / on the beginning
        Given I have directory with the name "/new_dir"
        When  I move the item to "new_dir"
        Then  I insure that new full name is "/new_dir/0000000162.jpg"
