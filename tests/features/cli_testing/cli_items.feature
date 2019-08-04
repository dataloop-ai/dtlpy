#noinspection CucumberUndefinedStep
Feature: Cli Items

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set to development
        And I am logged in
        And Environment is "dev"
        And I have context random number

    Scenario: Items ls
        When I perform command:
            |projects|create|-p|cli_items_project_<random>|
        And I succeed
        Then I wait "4"
        When I perform command:
            |datasets|create|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|
        And I succeed
        And I perform command:
            |items|ls|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|
        Then I succeed

  Scenario: Items upload - maximum param given
        When I perform command:
            |items|upload|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-l|<rel_path>/upload_batch/to_upload|-lap|<rel_path>/annotations_for_cli_upload|-nw|32|-f|.jpg,.png|-r|/items|-rp|
        Then I succeed

    Scenario: Items upload - minimum param given
        When I perform command:
            |items|upload|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-l|<rel_path>/upload_batch/to_upload|-ow
        Then I succeed

    Scenario: Items download - maximum param given
        When I perform command:
            |items|download|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-l|<rel_path>/cli_dataset_download|-ao|mask,instance,json|-nw|32|-r|/**|-rp|-th|-1|-wt|
        Then I succeed

    Scenario: Items download - minimum param given
        When I perform command:
            |items|download|-p|cli_items_project_<random>|-d|cli_items_dataset_<random>|-l|<rel_path>/cli_dataset_download|-ow
        Then I succeed

    Scenario: Finally
        Given I delete the project by the name of "cli_items_project_<random>"