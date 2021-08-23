#Feature: Features vectors repository create service testing
#
#  Background: Initiate Platform Interface and create a project
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    And There is a project by the name of "feature_create"
#    And I create a dataset with a random name
#    And I upload an item by the name of "test_item.jpg"
#
#  @feature.delete
#  @feature_set.delete
#  Scenario: Create a Feature set
#    When I create a feature sets with a random name
#    When I create a feature
#    Then Feature object should be exist
#    And Feature object should be exist in host
#    Then FeatureSet object should be exist
#    And FeatureSet object should be exist in host
#
#  @feature.delete
#  @feature_set.delete
#  Scenario: List Feature set
#    Given There are no feature sets
#    When I create a feature sets with a random name
#    And I create a feature
#    Then FeatureSet list have len 1
#    And Feature list have len 1