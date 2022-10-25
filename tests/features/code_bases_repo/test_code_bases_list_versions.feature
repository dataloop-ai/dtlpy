Feature: Codebases repository List Version method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "codebases_list_versions"
        And I create a dataset with a random name

    @testrail-C4523076
    Scenario: List all versions when 2 exist
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_list_versions"
        When I pack directory by name "codebase_name"
        And I modify python file - (change version) in path "codebases_assets/codebases_list_versions/some_code.py"
        And I pack directory by name "codebase_name"
        When I list versions of "codebase_name"
        Then I receive a list of "2" versions

    @testrail-C4523076
    Scenario: List all versions when 1 exist
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_list_versions"
        When I pack directory by name "codebase_name1"
        When I list versions of "codebase_name1"
        Then I receive a list of "1" versions

    @testrail-C4523076
    Scenario: List all versions when 0 exist
        When I list versions of "codebase_name2"
        Then I receive a list of "0" versions

