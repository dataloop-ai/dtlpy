Feature: Convert dpk entity to json and vice versa
  # Enter feature description here

    Background:
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_app_ins"

    @testrail-C4524925
    Scenario: Converting valid app.json to entity
        When I fetch the dpk from 'apps/app.json' file
        Then I have a dpk entity
        And I have json object to compare
        And The dpk is filled with the same values

    @testrail-C4524925
    Scenario: Converting a valid dpk entity to json object
        When I fetch the dpk from 'apps/app.json' file
        Then The dpk is filled with the same values
