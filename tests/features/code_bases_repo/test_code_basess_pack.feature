Feature: Codebases repository Pack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "codebases_pack"
        And I create a dataset with a random name

    Scenario: Unpack a Codebase (init param: dataset, project, client_api)
        Given Directory "codebases_pack_unpack" is empty
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_pack"
        When I pack directory by name "codebase_name1"
        Then I receive a Codebase object
        And Codebase in host when downloaded to "codebases_pack_unpack" equals code base in path "codebases_assets/codebases_pack"

    Scenario: Pack a Codebase (init param: project, client_api)
        Given Directory "codebases_pack_unpack" is empty
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_pack"
        When I pack directory by name "codebase_name2"
        Then I receive a Codebase object
        And Dataset by the name of "Binaries" was created
        And Codebase in host in dataset "Binaries", when downloaded to "codebases_pack_unpack" equals code base in path "codebases_assets/codebases_pack"

    Scenario: Pack a Codebase - new version
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_pack"
        When I pack directory by name "codebase_name3"
        And I modify python file - (change version) in path "codebases_assets/codebases_pack/some_code.py"
        And I pack directory by name "codebase_name3"
        Then There should be "2" versions of the code base "codebase_name3" in host
    
    Scenario: Pack a Codebase - new version - nameless
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_pack"
        When I pack directory - nameless
        And I modify python file - (change version) in path "codebases_assets/codebases_pack/some_code.py"
        And I pack directory - nameless
        Then There should be "2" versions of the code base "codebase" in host

