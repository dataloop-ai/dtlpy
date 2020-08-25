Feature: Upload and Download Numpy.Ndarray Item

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And There is a project by the name of "Project_test_annotation_add"
        And I create a dataset with a random name
        And I convert to Numpy.NdArray an item with the name "0000000162.jpg" and add it to context.array
        And I save item_metadata context.item_metadata
        And I remove log files

    Scenario: Upload jpg Numpy.NdArray item
        Given There are no items
        When I Upload an Numpy.NdArray (context.array) item with the name "0000000162_from_ndarray.jpg"
        Then Item is correctly uploaded to platform
        And  Log file does not exist

    Scenario: Upload png Numpy.NdArray item
        Given There are no items
        When I Upload an Numpy.NdArray (context.array) item with the name "0000000162_from_ndarray.png"
        Then Item is correctly uploaded to platform

    Scenario: Upload illegal Numpy.NdArray item
        Given There are no items
        When I Upload an Numpy.NdArray (context.array) item with the name "0000000162_from_ndarray.abc"
        Then There are no items

    Scenario: Download Image as Numpy.NdArray
        Given There are no items
        When I Upload an Numpy.NdArray (context.array) item with the name "0000000162_from_ndarray.jpg"
        And  I Download as Numpy.NdArray the uploaded item
        Then Download Numpy.NdArray item and context.array size equal

    Scenario: Download some images as Numpy.NdArray
        Given There are no items
        When I Upload an Numpy.NdArray (context.array) item with the name "0000000162_from_ndarray.jpg"
        And  I Download as Numpy.NdArray the uploaded item
        Then Download Numpy.NdArray item and context.array size equal

    Scenario: Try to Download video as Numpy.NdArray
        Given There is one .mp4 item
        When  Download as Numpy.NdArray the .mp4
        Then  Log file is exist
