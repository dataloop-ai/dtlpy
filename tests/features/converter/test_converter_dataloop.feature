Feature: Converter dataloop format

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "dataloop_converter"

   @converter.platform_dataset.delete
   @testrail-C4523081
   Scenario: Convert platform dataloop dataset to yolo
       Given There is a local "dataloop" dataset in "converter/dataloop/local_dataset"
       And There is a platform dataloop dataset from "converter/dataloop/local_dataset"
       And Local path in "converter/dataloop/convert" is clean
       When I convert platform dataset to "yolo" in path "converter/dataloop/convert"
       Then Converted "yolo" dataset in "converter/dataloop/convert" is equal to dataset in "converter/yolo/dataloop_should_be"

   @converter.platform_dataset.delete
   @testrail-C4523081
   Scenario: Convert platform dataloop dataset to voc
       Given There is a local "dataloop" dataset in "converter/dataloop/local_dataset"
       And There is a platform dataloop dataset from "converter/dataloop/local_dataset"
       And Local path in "converter/dataloop/convert" is clean
       When I convert platform dataset to "voc" in path "converter/dataloop/convert"
       Then Converted "voc" dataset in "converter/dataloop/convert/voc/images" is equal to dataset in "converter/voc/dataloop_should_be/voc/images"

  @converter.platform_dataset.delete
  @testrail-C4523081
  Scenario: Convert platform dataloop dataset to coco
      Given There is a local "dataloop" dataset in "converter/dataloop/local_dataset"
      And There is a platform dataloop dataset from "converter/dataloop/local_dataset"
      And Local path in "converter/dataloop/convert" is clean
      Then I wait "30"
      When I convert platform dataset to "coco" in path "converter/dataloop/convert"
      Then Converted "coco" dataset in "converter/dataloop/convert/coco.json" is equal to dataset in "converter/coco/dataloop_should_be/coco.json"
