Feature: Webm Converter service testing - failed message

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "project_failed_video"
        And I create a dataset with a random name
        When Add Members "annotator1@dataloop.ai" as "annotator"
        And Add Members "annotator2@dataloop.ai" as "annotator"

    @testrail-C4532774
    Scenario: Video with wrong FPS should display message and have success execution status
        Given Item in path "webm-converter/failed_video.mp4" is uploaded to "Dataset"
        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        When I wait for video services to finish
        Then I validate execution status item metadata have the right message
