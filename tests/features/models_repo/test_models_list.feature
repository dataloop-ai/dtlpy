Feature: Model repository query testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "models_list"
        And I create a dataset by the name of "models_dataset" in the project

    @testrail-C4525320
    Scenario: List by model name
        When I push "first" package
             |codebase_id=None|package_name=test-package|src_path=packages_create|inputs=None|outputs=None|
        And I create "6" models
        When I list models with filter field "name" and values "model-num-1"
        Then I get "1" entities

