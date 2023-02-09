Feature: Upload annotation note with messages

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "note_annotation_with_messages project"
        And I create a dataset by the name of "note_annotation_with_messages dataset" in the project

    @testrail-C4533541
    Scenario: Upload note annotation with messages - image item
        Given I upload an item of type "bmp image" to the dataset
        And I upload note annotation to the item with the params
            | Parameter  | Value                    |
            | top        | 10                       |
            | left       | 10                       |
            | bottom     | 100                      |
            | right      | 100                      |
            | label      | 10                       |
            | messages   | ['message1', 'message2'] |
        Then I will see the on the note annotations the following messages
            | Parameter | Value                    |
            | messages  | ['message1', 'message2'] |

    @testrail-C4533541
    Scenario: Upload note annotation with messages - video item
        Given I upload an item of type "webm video" to the dataset
        And I upload note annotation to the item with the params
            | Parameter      | Value                     |
            | top            | 10                        |
            | left           | 10                        |
            | bottom         | 100                       |
            | right          | 100                       |
            | label          | 10                        |
            | messages       | ['message1', 'message2']  |
            | object_id      | 1                         |
            | frame_num      | 5                         |
            | end_frame_num  | 10                        |
        Then I will see the on the note annotations the following messages
            | Parameter | Value                    |
            | messages  | ['message1', 'message2'] |
