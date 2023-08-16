@qa-nightly
Feature: Projects repository create service testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch

    @testrail-C4523146
    @DAT-46593
    Scenario: Create project with legal name
        When I create a project by the name of "to-delete-test-project_create"
        Then Project object by the name of "to-delete-test-project_create" should be created
        And Project should exist in host by the name of "to-delete-test-project_create"


    @testrail-C4523146
    @DAT-46593
    Scenario: Create project with an existing project name
        When I try to create a project by the name of "to-delete-test-project_create_same_name"
        When I try to create a project by the name of "to-delete-test-project_create_same_name"
        Then "BadRequest" exception should be raised
        And Error message includes "Failed to create project"


    @testrail-C4523146
    @DAT-46593
    Scenario: Create project with illegal special characters
        When I try to create a project by the name of "¤¶§!#$%%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~ÇüéâäàåçêëèïîìæÆôöòûùÿ¢£¥PƒáíóóúñÑ¿¬½¼¡«»¦ßµ±°•·²€„…†‡ˆ‰Š‹Œ‘’“”–—˜™š›œŸ¨©®¯³´¸¹¾ÀÁÂÃÄÅÈÉÊËÌÍÎÏÐÒÓÔÕÖ×ØÙÚÛÜÝÞãðõ÷øüýþ"
        Then "BadRequest" exception should be raised


    @testrail-C4523146
    @DAT-46593
    Scenario: Create project with legal special characters
        When I create a project by the name of "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-[]|.,"
        Then Project object by the name of "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-[]|.," should be created
        And Project should exist in host by the name of "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-[]|.,"

