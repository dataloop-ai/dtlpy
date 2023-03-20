Feature: XRay integration

    Background: Background name
        Given Some initial setup

    @DAT-44223
    Scenario: Foo
        When creating foo
        Then return foo

    @DAT-44181
    Scenario: Bar
        Given existing foo
        When creating bar
        Then return bar
        And foo