Feature: Get Item _src_item

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "item_src"
    And I create a dataset with a random name
    Given There are "3" items
    And I save dataset items to context
    When Add Members "annotator1@dataloop.ai" as "annotator"
    And Add Members "annotator2@dataloop.ai" as "annotator"

  @DAT-54344
  Scenario: Get src_item from consensus item
    When I create Task
      | task_name=min_params | due_date=auto | assignee_ids=auto | consensus_percentage=auto | consensus_assignees=auto | scoring=False |
    And I get a consensus item
    Then I validate _src_item is not None


  @DAT-54344
  Scenario: Get src_item from cloned item has correct src item
    Given Item in path "0000000162.jpg" is uploaded to "Dataset"
    When I clone an item
    Then I validate cloned item has the correct src item


  @DAT-76433
  Scenario: clone failed etl item run image pre
    Given Item in path "faledetl.jpg" is uploaded to "Dataset"
    When I clone an item
    Then I validate image pre run on cloned item