Feature: Items advanced browser filters

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I create a project by the name of "items_list"
        And I create a dataset with a random name
        And Dataset ontology has attributes "attr1" and "attr2"
        Then Add Multiple Labels "dog", "cat", "object"




    @testrail-C4526499
    @DAT-46527
    Scenario: List with filters
        Given There are items, path = "filters/image.jpg"
            |directory={"/": 3, "/dir1/": 3, "/dir1/dir2/": 3}|annotated_label={"dog": 3, "cat": 3}|annotated_type={"box": 3, "polygon": 3}|name={"dog":3, "cat":3}|metadata={"user.good": 3, "user.bad": 3}|

#        Then I add attribute to items with box annotations

        When I create filters
        And I add field "metadata.system.size" with values "51200" and operator "gt"
        And I add field "metadata.system.size" with values "61440" and operator "lt"
        And I list items with filters
        Then I receive "33" items

#         single filter with join

        When I create filters
        And I add field "annotated" with values "True" and operator "None"
        And I add field "filename" with values "/*" and operator "None"
        And I join field "creator" with values "oa-test-1@dataloop.ai,oa-test-3@dataloop.ai,oa-test-4@dataloop.ai" and operator "in"
        And I join field "label" with values "cat" and operator "in"
        And I list items with filters
        Then I receive "3" items

        When I create filters
        And I convert "2" days ago to timestamp
        And I add field "createdAt" with values "timestamp" and operator "gt"
        And I add field "createdAt" with values "timestamp" and operator "lt"
        And I list items with filters
        Then I receive "33" items

        When I create filters
        And I add field "metadata.system.mimetype" with values "image/jpeg" and operator "None"
        And I join field "metadata.system.coordinateVersion" with values "v2" and operator "None"
        And I list items with filters
        Then I receive "3" items

#        When I create filters
#        And I join field "metadata.system.attributes" with values "{"1":"attr1"}" and operator "None"
#        And I list items with filters
#        Then I receive "3" items
#
#        When I create filters
#        And I join field "metadata.system.attributes" with values "{}" and operator "None"
#        And I list items with filters
#        Then I receive "9" items


