# @bot.create
# Feature: Triggers repository update service testing

# Background: Initiate Platform Interface and create a project
#     Given Platform Interface is initialized as dlp and Environment is set according to git branch
#     And I create a project by the name of "triggers_update"
#     And I create a dataset with a random name
#     And There is a package (pushed from "triggers/item") by the name of "triggers-update"
#     And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
#     And I create a trigger
#         | name=triggers-update | filters=None | resource=Item | action=Created | active=True | executionMode=Once |

# @services.delete
# @packages.delete
# Scenario: Update trigger

#     When I update trigger
#         | filters={"$and": [{"dir": {"$in": ["/trigger_dir"]}}]} |
#     Then I receive an updated Trigger object
#     And Trigger attributes are modified
#         | filters={"$and": [{"dir": {"$in": ["/trigger_dir"]}}]} |
#     And Trigger works only on items in "/trigger_dir"

#     When I update trigger
#         | active=False |
#     Then I receive an updated Trigger object
#     And Trigger attributes are modified
#         | active=False  |
#     Then Trigger is inactive

#     When I update trigger
#         | active=True |
#     Then I receive an updated Trigger object
#     And Trigger attributes are modified
#         | active=True  |
#     Then Trigger works only on items in "/trigger_dir"

#     When I update trigger
#         | filters={} | action=Updated |
#     Then I receive an updated Trigger object
#     And Trigger attributes are modified
#         | filters={} | action=Updated |
#     And Trigger works only on items updated

#     When I try to update trigger
#         | executionMode=Always |
#     Then "BadRequest" exception should be raised
