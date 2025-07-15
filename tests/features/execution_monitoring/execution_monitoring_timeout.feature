@bot.create
Feature: Execution Monitoring

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_execution_monitoring_timeout"

    @services.delete
    @packages.delete
    @DAT-97389
    Scenario: Timeout - failed
        When I push and deploy package with param "failed" in "execution_monitoring/timeout"
        And I execute
        Then Execution "failed" on timeout

    @services.delete
    @packages.delete
    @DAT-97390
    Scenario: Timeout - rerun
        When I push and deploy package with param "rerun" in "execution_monitoring/timeout"
        And I execute
        Then Execution "rerun" on timeout
