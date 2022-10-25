#Feature: Features vectors repository get service testing
#
#    Background: Initiate Platform Interface and create a pipeline
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And I create a project by the name of "feature_get"
#        And I create a dataset with a random name
#        And I upload an item by the name of "test_item.jpg"
#
#    @feature.delete
#    @feature_set.delete
#    @testrail-C4523107
#    Scenario: To Json
#        When I create a feature sets with a random name
#        When I create a feature
#        Then Object "Feature" to_json() equals to Platform json.
#        Then Object "Feature_Set" to_json() equals to Platform json.
#
#    @feature.delete
#    @feature_set.delete
#    @testrail-C4523107
#    Scenario: get Feature
#        When I create a feature sets with a random name
#        When I create a feature
#        And I get feature sets
#        And I get feature
#        Then It is equal to feature sets created
#        Then It is equal to feature created
