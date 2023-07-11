Feature: Platform Urls Tests

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "platform_urls"
        And I create a dataset with a random name
        And Item in path "0000000162.jpg" is uploaded to "Dataset"

    @testrail-C4532781
    @DAT-46592
    Scenario: Check project platform_url
        Then  I validate the platform url "project.platform_url" works

    @testrail-C4532781
    @DAT-46592
    Scenario: Check dataset platform_url
        Then  I validate the platform url "dataset.platform_url" works
        Then  I validate the platform url "project.dataset.platform_url" works

    @testrail-C4532781
    @DAT-46592
    Scenario: Check item platform_url
        Then  I validate the platform url "item.platform_url" works
        Then  I validate the platform url "dataset.item.platform_url" works
        Then  I validate the platform url "project.dataset.item.platform_url" works
