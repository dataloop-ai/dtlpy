#Feature: Pipeline update testing
#
#     Background: Initiate Platform Interface
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And There is a project by the name of "test_pipeline_update"
#        And Directory "pipeline_update" is empty
#
#     @pipelines.delete
#     Scenario: Update pipeline
#         When I create a pipeline with name "testpipelineupdate"
#         And I update pipeline description
#         Then Pipeline received equals Pipeline changed except for "description"
