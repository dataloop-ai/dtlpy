Feature: Pipeline entity method testing

#  Background: Initiate Platform Interface and create a pipeline
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    And There is a project by the name of "test_pipeline_sanity"
#    And I create a dataset with a random name
#    When I create a new plain recipe
#    And I update dataset recipe to the new recipe
#    Then Add Members "annotator1@dataloop.ai"
#
#  @pipelines.delete
##  @testrail-C4525314
#  Scenario: pipeline sanity all nodes type
#    When I create a package and service to pipeline
#    And I create a pipeline from pipeline-sanity
#    And There are "20" items
#    Then I wait "10"
#    When I update items status to custom task actions "fix-label" "fix-ann" "fix-cor"
#    Then I wait "7"
#    When I update items status to default task actions
#    Then I wait "7"
#    When I update items status to default qa task actions
#    Then I wait "7"
#    Then verify pipeline sanity result
#
#  @pipelines.delete
##  @testrail-C4525314
#  Scenario: pipeline delete use sdk
#    When I create a package and service to pipeline
#    And I create a pipeline from json
#    And I update the pipeline nodes
#    And check pipeline nodes