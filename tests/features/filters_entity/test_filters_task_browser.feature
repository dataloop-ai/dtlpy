Feature: Items task browser filters

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "items_list"
        And I create a dataset with a random name
        And Dataset ontology has attributes "attr1" and "attr2"
        Then Add Multiple Labels "dog", "cat", "object"


    @testrail-C4526503
    Scenario:
        Given There are items, path = "filters/image.jpg"
            |directory={"/": 3, "/dir1/": 3, "/dir1/dir2/": 3}|annotated_label={"dog": 3, "cat": 3}|annotated_type={"box": 3, "polygon": 3}|name={"dog":3, "cat":3}|metadata={"user.good": 3, "user.bad": 3}|

        # All tasks filter

        When I create Task
            | task_name=min_params | due_date=auto | assignee_ids=auto |
        Then I receive a task entity
        When I create filters
        And I add field "metadata.system.refs.type" with values "task" and operator "eq"
        And I list items with filters
        Then I receive "33" items

        # No task assignment

        When I create filters
        And I add field "metadata.system.refs.type" with values "task" and operator "ne"
        And I list items with filters
        Then I receive "0" items

        # Specific task

        When I create filters
        And I add field "metadata.system.refs.id" with values "task.id" and operator "in"
        And I list items with filters
        Then I receive "33" items


        # Specific task with status from today

        When I create filters
        And I convert "2" days ago to timestamp
        And I update items status to default task actions
        And I use custom filter for Specific task and status from today
        And I list items with filters
        Then I receive "12" items

        # Specific task and annotation-type (join)

        When I create filters
        And I add field "metadata.system.refs.type" with values "task" and operator "eq"
        And I join field "label" with values "cat" and operator "ne"
        And I list items with filters
        Then I receive "9" items