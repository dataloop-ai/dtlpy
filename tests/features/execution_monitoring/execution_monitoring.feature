@bot.create
Feature: Execution Monitoring

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "test_execution_monitoring"

    @services.delete
    @packages.delete
    Scenario: Kill Thread
        When I push and deploy package with param "None" in "execution_monitoring/kill_thread"
        And I execute
        And I terminate execution
        Then Execution was terminated

    @services.delete
    @packages.delete
    Scenario: Kill Process
        When I push and deploy package with param "None" in "execution_monitoring/run_as_process"
        And I execute
        And I terminate execution
        Then Execution was terminated

    @services.delete
    @packages.delete
    Scenario: Timeout - failed
        When I push and deploy package with param "failed" in "execution_monitoring/timeout"
        And I execute
        Then Execution "failed" on timeout

    @services.delete
    @packages.delete
    Scenario: Timeout - rerun
        When I push and deploy package with param "rerun" in "execution_monitoring/timeout"
        And I execute
        Then Execution "rerun" on timeout