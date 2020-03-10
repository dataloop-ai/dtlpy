Feature: Items repository list service testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "items_list"
        And I create a dataset with a random name

    Scenario: List with filters
        Given There are items, path = "filters/image.jpg"
            |directory={"/": 3, "/dir1/": 3, "/dir1/dir2/": 3}|annotated_label={"dog": 3, "cat": 3}|annotated_type={"box": 3, "polygon": 3}|name={"dog":3, "cat":3}|metadata={"user.good": 3, "user.bad": 3}|
        
        # single filter

        When I create filters
        And I add field "filename" with values "/dir1/*" and operator "glob"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "filename" with values "/dir1/**" and operator "glob"
        And I list items with filters
        Then I receive "6" items

        When I create filters
        And I add field "filename" with values "/**" and operator "glob"
        And I list items with filters
        Then I receive "33" items

        When I create filters
        And I add field "filename" with values "/dir1/dir2/*" and operator "glob"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I list items with filters
        Then I receive "12" items

        When I create filters
        And I add field "annotated" with values "False" and operator "None"
        And I list items with filters
        Then I receive "21" items

        When I create filters
        And I add field "name" with values "*dog*" and operator "glob"
        And I list items with filters
        Then I receive "6" items

        # When I create filters
        # And I add field "name" with values "!*dog*" and operator "glob"
        # And I list items with filters
        # Then I receive "27" items

        When I create filters
        And I add field "name" with values "*cat*" and operator "glob"
        And I list items with filters
        Then I receive "6" items

        # When I create filters
        # And I add field "name" with values "!*cat*" and operator "glob"
        # And I list items with filters
        # Then I receive "27" items

        When I create filters
        And I add field "metadata.user.good" with values "True" and operator "None"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "metadata.user.bad" with values "True" and operator "None"
        And I list items with filters
        Then I receive "3" items

        # single filter with join

        When I create filters
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "type" with values "box" and operator "None"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I join field "type" with values "segment" and operator "None"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "type" with values "box" and operator "ne"
        And I list items with filters
        Then I receive "9" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I join field "type" with values "segment" and operator "ne"
        And I list items with filters
        Then I receive "9" items

        When I create filters
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "label" with values "cat" and operator "None"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I join field "label" with values "dog" and operator "None"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "label" with values "cat" and operator "ne"
        And I list items with filters
        Then I receive "9" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I join field "label" with values "dog" and operator "ne"
        And I list items with filters
        Then I receive "9" items

        # multiple filters

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*label*" and operator "glob"        
        And I list items with filters
        Then I receive "6" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*type*" and operator "glob"        
        And I list items with filters
        Then I receive "6" items

        # When I create filters
        # And I add field "annotated" with values "True" and operator "None"
        # And I add field "filename" with values "/**" and operator "glob"
        # And I add field "name" with values "!*label*" and operator "glob"
        # And I list items with filters
        # Then I receive "6" items

        # When I create filters
        # And I add field "annotated" with values "True" and operator "None"
        # And I add field "filename" with values "/**" and operator "glob"
        # And I add field "name" with values "!*type*" and operator "glob"
        # And I list items with filters
        # Then I receive "6" items

        # multiple filters with join

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*label*" and operator "glob"
        And I join field "label" with values "dog" and operator "ne"
        And I join field "type" with values "point" and operator "None"         
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*label*" and operator "glob"
        And I join field "label" with values "cat" and operator "ne"
        And I join field "type" with values "point" and operator "None"        
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "type" with values "point" and operator "None"
        And I join field "label" with values "dog" and operator "ne"        
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I join field "type" with values "point" and operator "None"
        And I join field "label" with values "cat" and operator "ne"     
        And I list items with filters
        Then I receive "3" items

        # update

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*label*" and operator "glob"
        And I join field "label" with values "dog" and operator "ne"
        And I join field "type" with values "point" and operator "None"
        And I list items with filters
        Then I receive "3" items         
        When I update items with filters, field "updated"
        And I create filters
        And I add field "metadata.user.updated" with values "True" and operator "None"
        Then I receive "3" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I list items with filters
        Then I receive "12" items         
        When I update items with filters, field "annotated"
        And I create filters
        And I add field "metadata.user.annotated" with values "True" and operator "None"
        Then I receive "12" items

        # delete

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/**" and operator "glob"
        And I add field "name" with values "*label*" and operator "glob"
        And I join field "label" with values "dog" and operator "ne"
        And I join field "type" with values "point" and operator "None"
        And I list items with filters
        Then I receive "3" items         
        When I delete items with filters
        And I list items with filters
        Then I receive "0" items
        When I create filters
        And I list items with filters
        Then I receive "30" items

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I list items with filters
        Then I receive "9" items         
        When I delete items with filters
        And I create filters
        And I list items with filters
        Then I receive "21" items