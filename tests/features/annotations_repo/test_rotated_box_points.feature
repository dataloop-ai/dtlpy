Feature: Rotated box points testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        When I create two project  and datasets by the name of "rotated_box_off" "rotated_box_on"
        When I upload item in "0000000162.jpg" to both datasets

    @testrail-C4532243
    Scenario: Check rotated box geo with flag off
        Given I create 4ptBox setting to the "first" project
        And I set 4ptBox setting project setting to "False"
        When I upload rotated box annotation to item "1"
        Then The Geo will be of the "old" format

    @testrail-C4532243
    Scenario: Check rotated box geo with flag on
        Given I create 4ptBox setting to the "second" project
        And I set 4ptBox setting project setting to "True"
        When I upload rotated box annotation to item "2"
        Then The Geo will be of the "new" format


