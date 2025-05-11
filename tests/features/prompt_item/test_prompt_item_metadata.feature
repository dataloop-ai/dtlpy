Feature: Prompt Item Entity

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "prompt_item_tests"
        And I create a dataset with a random name
        And There is a JSON item

    @DAT-90109
    Scenario: Create prompt item and add metadata
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2}
        When I update the prompt item
        Then The prompt item metadata equals {"meta": 1, "data": 2}

    @DAT-90109
    Scenario: Add prompt metadata and update
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2}
        And I update the prompt item
        When I set prompt item metadata to {"meta": 3, "data": 4}
        Then The prompt item metadata equals {"meta": 3, "data": 4}

    @DAT-90109
    Scenario: Get and update existing metadata
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2}
        And I update the prompt item
        When I get the prompt item metadata
        Then The prompt item metadata equals {"meta": 1, "data": 2}
        And I set prompt item metadata to {"meta": 5, "data": 6}
        Then The prompt item metadata equals {"meta": 5, "data": 6}

    @DAT-90109
    Scenario: Delete prompt item
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2}
        And I update the prompt item
        When I delete the prompt item
        Then The prompt item "test_prompt_item.json" does not exist in the dataset

    @DAT-90109
    Scenario: Add new metadata key-value pair
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2}
        And I update the prompt item
        When I add metadata key "new_key" with value "new_value"
        Then The prompt item metadata equals {"meta": 1, "data": 2, "new_key": "new_value"}

    @DAT-90109
    Scenario: Delete metadata key
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2, "key_to_delete": "value"}
        And I update the prompt item
        When I delete metadata key "key_to_delete"
        Then The prompt item metadata equals {"meta": 1, "data": 2}

    @DAT-90109
    Scenario: Update metadata key value
        Given I create a prompt item with name "test_prompt_item.json"
        And I set prompt item metadata to {"meta": 1, "data": 2, "key_to_update": "old_value"}
        And I update the prompt item
        When I update metadata key "key_to_update" with value "new_value"
        Then The prompt item metadata equals {"meta": 1, "data": 2, "key_to_update": "new_value"}
