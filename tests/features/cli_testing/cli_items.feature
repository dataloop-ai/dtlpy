#noinspection CucumberUndefinedStep
Feature: Cli Items

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I am logged in
        And I have context random number

    @testrail-C4523069
    @DAT-46477
    Scenario: Items ls
        When I perform command:
            |projects|create|-p|to-delete-test-<random>_cli_items_project|
        And I succeed
        Then I wait "4"
        When I perform command:
            |datasets|create|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|
        And I succeed
        And I perform command:
            |items|ls|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|
        Then I succeed

  @testrail-C4523069
  @DAT-46477
  Scenario: Items upload - maximum param given
        When I perform command:
            |items|upload|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|-l|<rel_path>/upload_batch/to_upload|-lap|<rel_path>/annotations_for_cli_upload|-f|.jpg,.png|-r|/items|-rp|
        Then I succeed

    @testrail-C4523069
    @DAT-46477
    Scenario: Items upload - minimum param given
        When I perform command:
            |items|upload|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|-l|<rel_path>/upload_batch/to_upload|-ow
        Then I succeed

    @testrail-C4523069
    @DAT-46477
    Scenario: Items download - maximum param given
        When I perform command:
            |items|download|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|-l|<rel_path>/cli_dataset_download|-ao|mask,instance,json|-r|/**|-rp|-th|-1|-wt|
        Then I succeed

    @testrail-C4523069
    @DAT-46477
    Scenario: Items download - minimum param given
        When I perform command:
            |items|download|-p|to-delete-test-<random>_cli_items_project|-d|test_<random>_cli_items_dataset|-l|<rel_path>/cli_dataset_download|-ow
        Then I succeed

    @testrail-C4523069
    @DAT-46477
    Scenario: Finally
        Given I delete the project by the name of "to-delete-test-<random>_cli_items_project"
