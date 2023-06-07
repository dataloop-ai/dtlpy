#Feature: ML Pipeline entity method testing
#
#    Background: Initiate Platform Interface and create a ml pipeline
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And I create a project by the name of "test_ml_pipeline_flow"
#        And I create a dataset with a random name
#        When I create a new plain recipe
#        And I update dataset recipe to the new recipe
#        And I push "first" package
#            | codebase_id=None | package_name=test-package | src_path=package_module | inputs=None | outputs=None | type=ml |
#
#    @pipelines.delete
#    @DAT-48209
#    Scenario: pipeline predict ml node variable flow
#        Given I create a model with a random name
#        And I set dataset readonly mode to "True"
#        And I update model status to "trained"
#        And Pipeline which have a model variable and predict ml node that reference to this model variable.
#        When I install pipeline in context
#        Then The pipeline installed successfully and model id placed correctly in the service initInputs
#        When I create a model with a random name
#        And I update model status to "trained"
#        And I update the model variable and the pipeline is still installed
#        Then The pipeline installed successfully and model id placed correctly in the service initInputs
