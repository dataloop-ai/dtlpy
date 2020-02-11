Feature: Codebases repository List method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "codebases_list"
        And I create a dataset with a random name

    Scenario: List all versions when 0 exist
        Given There are "0" code bases
        When I list all code bases
        Then I receive a list of "0" code bases

    Scenario: List all code bases when 1 exist
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_list"
        When I pack directory by name "codebase1_name"
        When I list all code bases
        Then I receive a list of "1" code bases

    Scenario: List all code bases when 2 exist
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_list"
        And I pack directory by name "codebase2_name"
        When I list all code bases
        Then I receive a list of "2" code bases

    Scenario: List all versions when 3 exist
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_list"
        And There are "2" code bases
        When I pack directory by name "codebase_name3"
        When I list all code bases
        Then I receive a list of "3" code bases

