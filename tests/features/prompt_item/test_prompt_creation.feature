Feature: Prompt Item Creation and Management

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "prompt_item_tests"
        And I create a dataset with a random name
        And There is a JSON item

    @DAT-90561
    Scenario: Create prompt item with text prompt
        Given I create a prompt item with name "text_prompt.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "Who are you?"
        And I add the prompt to the prompt item
        When I update the prompt item
        Then The prompt item contains text prompt "Who are you?"

    @DAT-90561
    Scenario: Create prompt item with image prompt
        Given I create a prompt item with name "image_prompt.json"
        And I create a prompt with key "conversation-1"
        And I add image element to prompt with value "https://example.com/image.png"
        And I add the prompt to the prompt item
        When I update the prompt item
        Then The prompt item contains image prompt

    @DAT-90561
    Scenario: Create prompt item with multiple prompts
        Given I create a prompt item with name "multi_prompt.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "First question"
        And I add the prompt to the prompt item
        And I create a prompt with key "conversation-2"
        And I add text element to prompt with value "Second question"
        And I add the prompt to the prompt item
        When I update the prompt item
        Then The prompt item contains "2" prompts
        And The prompt item contains text prompt "First question"
        And The prompt item contains text prompt "Second question"

    @DAT-90561
    Scenario: Create prompt item with mixed content
        Given I create a prompt item with name "mixed_prompt.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "What's in this image?"
        And I add image element to prompt with value "https://example.com/image.png"
        And I add the prompt to the prompt item
        When I update the prompt item
        Then The prompt item contains text prompt "What's in this image?"
        And The prompt item contains image prompt 