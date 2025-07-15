@bot.create
Feature: Execution Monitoring

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "test_execution_monitoring_terminate"

    @services.delete
    @packages.delete
    @DAT-46522
    Scenario: Kill Thread
        When I push and deploy package with param "None" in "execution_monitoring/kill_thread"
        And I execute
        And I terminate execution
        Then Execution was terminated with error message "termination signal"

    @services.delete
    @packages.delete
    @DAT-97388
    Scenario: Kill Process
        When I push and deploy package with param "None" in "execution_monitoring/run_as_process"
        And I execute
        And I terminate execution
        Then Execution was terminated with error message "killed"
