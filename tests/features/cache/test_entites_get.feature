#Feature: cache get
#
#  Background: Initiate Platform Interface and create a project
#    When set binary cache size to 10
#    Given cache is on
#    Given Platform Interface is initialized as dlp and Environment is set according to git branch
#    Given I create a project by the name of "cachetest"
#
#
#  Scenario: Get an entities from cache
#    When I create a dataset with a random name
#    Then i make dataset get and i get hit
#    When I upload a file in path "assets_split/items_upload/0000000162.jpg"
#    Then i make item get and i get hit
#    Then I upload a annotation for the item
#    And i make annotation get and i get hit
#    When I delete the item by id
#    And I delete the dataset that was created by id
#    Then i make dataset get and i get miss
#    Then i make item get and i get miss
#    And i make annotation get and i get miss
#    Then cache is off
#
#  Scenario: download item
#    When I create a dataset with a random name
#    When I upload a file in path "assets_split/items_upload/0000000162.jpg"
#    Then I download the item
#    And I git cache bin hit
#    Then cache is off
#
#  Scenario: update item
#    When I create a dataset with a random name
#    When I upload a file in path "assets_split/items_upload/0000000162.jpg"
#    When I update item system metadata with system_metadata="True"
#    Then i make item get and i get hit
#    And Item was updated
#    Then cache is off
#
#  Scenario: list item
#    When I create a dataset with a random name
#    When I upload a file in path "assets_split/items_upload/0000000162.jpg"
#    When I list items
#    Then i make item get and i get hit
#    Then cache is off
#
#  Scenario: Get an bilk from cache and lru
#    When I create a dataset with a random name
#    Then i make dataset get and i get hit
#    When I upload a file in path "cache/100"
#    Then i make all item get and i get hit
#    And the lru is work
#    When I delete the dataset that was created by id
#    Then i make dataset get and i get miss
#    Then i make all item get and i get miss
#    Then cache is off