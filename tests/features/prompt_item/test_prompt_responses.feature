Feature: Prompt Item Responses and Annotations

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "prompt_item_tests"
        And I create a dataset with a random name
        And There is a JSON item

    @DAT-90561
    Scenario: Add text response to prompt
        Given I create a prompt item with name "text_response.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "Who are you?"
        And I add the prompt to the prompt item
        And I update the prompt item
        When I add text response to prompt with model "blabla", key "conversation-1" and value "I am a bot"
        Then The prompt item contains text response "I am a bot"

    @DAT-90561
    Scenario: Add image response to prompt
        Given I create a prompt item with name "image_response.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "Show me a cat"
        And I add the prompt to the prompt item
        And I update the prompt item
        And I upload an image with name "converter/voc/local_voc_with_folders/items/DogeJPEG.jpeg"
        When I add image response to prompt with key "conversation-1" using the uploaded image
        Then The prompt item contains image response

    @DAT-90561
    Scenario: Add response with model info
        Given I create a prompt item with name "model_response.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "What is this?"
        And I add the prompt to the prompt item
        And I update the prompt item
        When I add text response to prompt with model "blabla", key "conversation-1" and value "This is a test"
        Then The prompt item contains text response "This is a test"
        And The response has model info

    @DAT-90561
    Scenario: Add multiple responses to same prompt
        Given I create a prompt item with name "multiple_responses.json"
        And I create a prompt with key "conversation-1"
        And I add text element to prompt with value "What is this?"
        And I add the prompt to the prompt item
        And I update the prompt item
        When I add text response to prompt with model "model1", key "conversation-1" and value "First response"
        And I add text response to prompt with model "model2", key "conversation-1" and value "Second response"
        Then The prompt item contains text response "First response"
        And The prompt item contains text response "Second response"