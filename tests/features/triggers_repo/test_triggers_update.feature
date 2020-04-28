# TODO - Move from comment after issac fixes PLUG-153
# @bot.create
# Feature: Triggers repository update service testing

#     Background: Initiate Platform Interface and create a project
#         Given Platform Interface is initialized as dlp and Environment is set according to git branch
#         And There is a project by the name of "triggers_update"
#         And I create a dataset with a random name
#         And There is a package (pushed from "triggers/item") by the name of "triggers_update"
#         And There is a service by the name of "triggers-update" with module name "default_module" saved to context "service"
#         And I create a trigger
#             |name=triggers_update|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

#     @services.delete
#     @packages.delete
#     Scenario: Update trigger
#         When I update trigger
#             |filters={"$and": [{"type": "file"}]}|active=False|
#         Then I receive an updated Trigger object
#         And Trigger attributes are modified
#             |filters={"$and": [{"type": "file"}]}|active=False|