Feature: Items repository list function testing

    # Background: Initiate Platform Interface and create a project
    #     Given Platform Interface is initialized as dlp and Environment is set to development
    #     And There is a project by the name of "items_list"
    #     And I create a dataset with a random name

    # Scenario: List with filters
    #     Given There are items
    #         |dir={"/": 3, "/dir1": 3, "/dir1/dir2": 3}|annotated_label={"dog": 3, "cat": 3}|annotated_type={"box": 3, "point": 3}|name={"dog":3, "cat":3}|metadata={"user.good": true, "user.bad": false}|
    #     When I create filters
    #     And I add field "" with values "" and operator ""
    #     And I list items
    #     Then I receive "" items

