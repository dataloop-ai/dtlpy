Feature: Codebase Entity repo services

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "codebase_repo_methods"
        And I create a dataset with a random name
        And There is a Codebase directory with a python file in path "codebases_assets/codebase_entity"
        And I pack from project.codebases directory by name "codebase_name"

    Scenario: Unpack by name
        When I unpack a code base entity by the name of "codebase_name" to "codebases_assets/codebase_entity_unpack"
        Then Unpacked code base equal to code base in "codebases_assets/codebase_entity"

    Scenario: List all versions when 2 exist
        When I modify python file - (change version) in path "codebases_assets/codebase_entity/some_code.py"
        Given I pack from project.codebases directory by name "codebase_name"
        When I list versions of code base entity "codebase_name"
        Then I receive a list of "2" versions

