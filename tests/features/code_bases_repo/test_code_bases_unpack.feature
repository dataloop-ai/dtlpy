Feature: Codebases repository Unpack method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "codebases_unpack"
        And I create a dataset with a random name

    @testrail-C4523077
     Scenario: Unpack by name
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name1"
         When I unpack a code base by the name of "codebase_name1" to "codebases_assets/codebase_unpack"
         Then Unpacked code base equal to code base in "codebases_assets/codebases_unpack"

    @testrail-C4523077
     Scenario: Unpack by id
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name2"
         When I unpack a code base by the id of "codebase_name2" to "codebases_assets/codebase_unpack"
         Then Unpacked code base equal to code base in "codebases_assets/codebases_unpack"

    @testrail-C4523077
     Scenario: Unpack non-existing by name
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name3"
         When I try to unpack a code base by the name of "some_name" to "codebases_assets/codebase_unpack"
         Then "NotFound" exception should be raised

    @testrail-C4523077
     Scenario: Unpack by non-existing id
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name4"
         When I try to unpack a code base by the id of "some_id" to "codebases_assets/codebase_unpack"
         Then "BadRequest" exception should be raised

    @testrail-C4523077
     Scenario: Unpack - specific version
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name5"
         And I modify python file - (change version) in path "codebases_assets/codebases_unpack/some_code.py"
         And I pack directory by name "codebase_name5"
         When I unpack a code base "codebase_name5" version "1" to "codebases_assets/codebase_unpack"
         Then Unpacked code base equal to code base in "codebases_assets/codebases_unpack"

    @testrail-C4523077
     Scenario: Unpack - latest version
         Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
         And I pack directory by name "codebase_name6"
         And I modify python file - (change version) in path "codebases_assets/codebases_unpack/some_code.py"
         And I pack directory by name "codebase_name6"
         When I unpack a code base "codebase_name6" version "latest" to "codebases_assets/codebase_unpack"
         Then Unpacked code base equal to code base in "codebases_assets/codebases_unpack"

    @testrail-C4523077
    Scenario: Unpack - all versions
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
        And I pack directory by name "codebase_name7"
        And I modify python file - (change version) in path "codebases_assets/codebases_unpack/some_code.py"
        And I pack directory by name "codebase_name7"
        When I unpack a code base "codebase_name7" version "all" to "codebases_assets/codebase_unpack"
        Then I receive all versions in "codebases_assets/codebase_unpack" and they are equal to versions in "codebases_assets/codebases_unpack/some_code.py"

    @testrail-C4523077
    Scenario: Unpack - non-existing version
        Given There is a Codebase directory with a python file in path "codebases_assets/codebases_unpack"
        And I pack directory by name "codebase_name8"
        And I modify python file - (change version) in path "codebases_assets/codebases_unpack/some_code.py"
        And I pack directory by name "codebase_name8"
        When I try to unpack a code base "codebase_name8" version "5" to "codebases_assets/codebase_unpack"
        Then "NotFound" exception should be raised

