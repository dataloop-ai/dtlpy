Feature: Datasets repository upload labels

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "datasets_upload_labels"

    @testrail-C4530465
    Scenario: Upload labels to dataset from csv
        When I create a dataset with a random name
        And I upload labels from csv file "label_in_csv.csv"
        Then I validate labels in recipe from file "label_in_csv.csv"