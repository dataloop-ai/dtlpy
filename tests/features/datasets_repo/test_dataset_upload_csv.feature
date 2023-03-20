Feature: Datasets repository - upload items & annotations from csv

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_download_annotations"
        And I create a dataset with a random name

    @DAT-44230
    Scenario: upload csv
        Given I upload csv "mycsv_all.csv" to dataset
        Then description in csv "mycsv_all.csv" equal to the description uploaded
        Then metadata in csv "mycsv_all.csv" equal to the metadata uploaded




