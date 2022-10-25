#Feature: Features vectors repository delete service testing
#
#    Background: Initiate Platform Interface and create a project
#        Given Platform Interface is initialized as dlp and Environment is set according to git branch
#        And I create a project by the name of "features_set_delete"
#        And I create a dataset with a random name
#        And I upload an item by the name of "test_item.jpg"
#
#    @testrail-C4523106
#    Scenario: Delete features set
#        Given There are no feature sets
#        When I create a feature sets with a random name
#        And I create a feature
#        When I delete the features that was created
#        Then features does not exists
#        When I delete the features set that was created
#        Then features set does not exists
