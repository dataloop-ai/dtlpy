import behave
import os
import filecmp
import json


@behave.then(u'I compare json annotations between the files in dirs')
def step_impl(context):
    context.annotation_json_dir = None
    context.item_json_dir = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "annotation_json_dir":
            context.annotation_json_dir = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "item_json_dir":
            context.item_json_dir = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

    # Function to compare annotation and item json files
    def compare_directory_annotations_json_files(dir1, dir2):
        dirs_cmp = filecmp.dircmp(dir1, dir2)
        if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
            return False

        # Compare files data
        for item in os.listdir(dir1):
            if item.endswith('.json'):
                file1_path = os.path.join(dir1, item)
                file2_path = os.path.join(dir2, item)

                with open(file1_path, 'r') as annotations_file1:
                    file1_json = json.load(annotations_file1)

                with open(file2_path, 'r') as annotations_file2:
                    file2_json = json.load(annotations_file2)

                # Comparing the sorted files
                assert file1_json == file2_json['annotations'][0], "mismatch data on file: " + item

        for common_dir in dirs_cmp.common_dirs:
            new_dir1 = os.path.join(dir1, common_dir)
            new_dir2 = os.path.join(dir2, common_dir)
            if not compare_directory_annotations_json_files(new_dir1, new_dir2):
                return False
        return True

    assert compare_directory_annotations_json_files(context.annotation_json_dir, context.item_json_dir)


@behave.then(u'I compare json metadata and annotationsCount between the files in dirs')
def step_impl(context):
    context.item_json_dir = None
    context.dataset_json_dir = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "item_json_dir":
            context.item_json_dir = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "dataset_json_dir":
            context.dataset_json_dir = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

    # Function to compare item and dataset json files
    def compare_directory_metadata_json_files(dir1, dir2):
        dirs_cmp = filecmp.dircmp(dir1, dir2)
        if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
            return False

        # Compare files data
        for item in os.listdir(dir1):
            if item.endswith('.json'):
                file1_path = os.path.join(dir1, item)
                file2_path = os.path.join(dir2, item)

                with open(file1_path, 'r') as annotations_file1:
                    file1_json = json.load(annotations_file1)

                with open(file2_path, 'r') as annotations_file2:
                    file2_json = json.load(annotations_file2)

                # Comparing the sorted files
                assert file1_json["metadata"] == file2_json["metadata"], "mismatch metadata on file: " + item
                assert len(file1_json["annotations"]) == file2_json["annotationsCount"], "mismatch annotationsCount on file: " + item

                if len(file1_json["annotations"]) == 0:
                    assert file2_json["annotated"] is False, "mismatch annotated on file: " + item
                else:
                    assert file2_json["annotated"] is True, "mismatch annotated on file: " + item

        for common_dir in dirs_cmp.common_dirs:
            new_dir1 = os.path.join(dir1, common_dir)
            new_dir2 = os.path.join(dir2, common_dir)
            if not compare_directory_metadata_json_files(new_dir1, new_dir2):
                return False
        return True

    assert compare_directory_metadata_json_files(context.item_json_dir, context.dataset_json_dir)
