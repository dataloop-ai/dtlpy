 Feature: Create test for dataset directory tree

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "dataset_dir_tree_test"

    @DAT-53904
    Scenario: Create dataset
        Given I create a dataset named "dir_tree_test"
        Then dataset.directory_tree.dir_names contains "/"
        And I upload an item by the name of "test_item.jpg"
        And I get an item thumbnail response
        And dataset.directory_tree.dir_names contains "/.dataloop"
        And dataset.directory_tree.dir_names contains "/.dataloop/thumbnails"


