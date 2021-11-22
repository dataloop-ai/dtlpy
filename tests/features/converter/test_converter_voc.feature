Feature: Converter voc format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "voc_converter"
        And I create a dataset with a random name

    @testrail-C4523082
    Scenario: Convert local voc dataset to dataloop
        Given There is a local "voc" dataset in "converter/voc/local_dataset"
        When I convert local "voc" dataset to "dataloop"
        Given Local path in "converter/voc/reverse" is clean
        When I reverse dataloop dataset to local "voc" in "converter/voc/reverse"
        Then local "voc" dataset in "converter/voc/local_dataset" is equal to reversed dataset in "converter/voc/reverse"