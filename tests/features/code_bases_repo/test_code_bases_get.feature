Feature: Codebases repository Get method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "codebases_get"
        And I create a dataset with a random name

    @testrail-C4523073
    @DAT-46481
    Scenario: Get code base by name
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_get"
        When I pack directory by name "codebase_name1"
        And I modify python file - (change version) in path "codebases_assets/codebases_get/some_code.py"
        And I pack directory by name "codebase_name1"
        When I get by name version "1" of code base "codebase_name1"
        Then I receive a Codebase object
        And Codebase received equal code base packet

    @testrail-C4523073
    @DAT-46481
    Scenario: Get code base by id
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_get"
        When I pack directory by name "codebase_name2"
        And I modify python file - (change version) in path "codebases_assets/codebases_get/some_code.py"
        And I pack directory by name "codebase_name2"
        When I get by id version "1" of code base "codebase_name2"
        Then I receive a Codebase object
        And Codebase received equal code base packet

    @testrail-C4523073
    @DAT-46481
    Scenario: Get code base by id - latest
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_get"
        When I pack directory by name "codebase_name3"
        And I modify python file - (change version) in path "codebases_assets/codebases_get/some_code.py"
        And I pack directory by name "codebase_name3"
        When I get by id version "latest" of code base "codebase_name3"
        Then I receive a Codebase object
        And Codebase received equal code base packet

    @testrail-C4523073
    @DAT-46481
    Scenario: Get code base by name - no version given
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_get"
        When I pack directory by name "codebase_name4"
        And I modify python file - (change version) in path "codebases_assets/codebases_get/some_code.py"
        And I pack directory by name "codebase_name4"
        When I get a code base by name "codebase_name4"
        Then I receive a Codebase object
        And Codebase received equal code base packet

    @testrail-C4523073
    @DAT-46481
    Scenario: Get code base by id - all
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_get"
        When I pack directory by name "codebase_name5"
        And I modify python file - (change version) in path "codebases_assets/codebases_get/some_code.py"
        And I pack directory by name "codebase_name5"
        When I get by name version "all" of code base "codebase_name5"
        Then I receive a list of Codebase objects
        And Codebase list have length of "2"


