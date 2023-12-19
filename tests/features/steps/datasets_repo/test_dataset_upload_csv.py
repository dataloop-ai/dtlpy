import time
import behave
import os
import json
import csv


@behave.given(u'I upload csv "{csv_file}" to dataset')
def step_impl(context, csv_file):
    csv_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], csv_file)
    context.item = context.dataset.items.upload(local_path=csv_file_path)

    with open(csv_file_path, "r") as file:
        line_count = len(file.readlines())

    # Wait for the upload and processing to process all lines
    # CSV file has extra line for the header but also dataset has extra item for the CSV file
    # Wait for processing to complete with a 5-minute timeout
    timeout = 60
    while (timeout != 0) and (len(context.dataset.items.get_all_items()) < line_count):
        print(f"Waiting for upload and processing to complete... Running for {10 * (60 - timeout):.2f}[s]")
        time.sleep(10)
        timeout -= 1

    assert timeout != 0, "Timeout. csv load failed to complete after 10 minutes"


@behave.then(u'description in csv "{csv_file}" equal to the description uploaded')
def step_impl(context, csv_file):
    csv_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], csv_file)
    with open(csv_file_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')

        # check the header row 7th column is indeed the "item_description"
        row = next(csvreader)
        assert (row[6] == 'item_description')

        for row in csvreader:
            # search for the right item base on name
            itemname = f"*{row[2]}*"
            filters = context.dl.Filters()
            filters.add(field='type', values='file')
            filters.add(field='name', values=itemname)
            pages = context.dataset.items.list(filters=filters)
            assert len(pages.items) == 1, f"TEST FAILED: Failed to find item by name: {itemname}"
            item = pages[0][0]

            # check the item description match the text in the seventh column
            assert (row[6] == item.description)


@behave.then(u'metadata in csv "{csv_file}" equal to the metadata uploaded')
def step_impl(context, csv_file):
    csv_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], csv_file)
    with open(csv_file_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')

        # check the header row 7th column is indeed the "item_metadata"
        row = next(csvreader)
        assert (row[5] == 'item_metadata')

        for row in csvreader:
            # search for the right item base on name
            itemname = f"*{row[2]}*"
            filters = context.dl.Filters()
            filters.add(field='type', values='file')
            filters.add(field='name', values=itemname)
            pages = context.dataset.items.list(filters=filters)
            assert len(pages.items) == 1, f"TEST FAILED: Failed to find item by name: {itemname}"
            item = pages[0][0]

            # check the item description match the text in the seventh column
            json_text = row[5]
            # parse the JSON text into a Python dictionary
            json_dict = json.loads(json_text)

            # iterate over the keys and values in the dictionary
            for key, value in json_dict.items():
                # if the value is a dictionary, iterate over its keys and values
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if not isinstance(sub_value, dict):
                            assert sub_key in item.metadata[key]
                            assert sub_value in item.metadata[key][sub_key]
                else:
                    assert value in item.metadata[key]
