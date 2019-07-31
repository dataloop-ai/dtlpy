# Feature: Checkouts

#   Background: Background
#     Given Platform Interface is initialized as dlp and Environment is set to development
#     And There is a project by the name of "items_download_batch"
#     And Get feature entities
#       |dataset|package|plugin|

#   Scenario: Feature entities
#     Given Feature: I create a dataset by the name of "Dataset"
#     And Feature: There is a Package directory with a python file in path "plugin_package"
#     And Feature: I pack to project directory in "plugin_package"
#     And Feature: There is a plugin

#   Scenario: Projects
#     When I checkout
#       |project|
#     Then I am checked out

#   Scenario: Projects
#     When I checkout
#       |dataset|
#     Then I am checked out

#   Scenario: Projects
#     When I checkout
#       |plugin|
#     Then I am checked out

#   Scenario: Finally
#     Given Clean up
