import behave
import dtlpy as dl
import pandas as pd
import os
import json


@behave.when(u'I upload labels from csv file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    labels_df = pd.read_csv(file_path)
    context.dataset.add_labels(label_list=labels_df["dataloop label"].to_list())


@behave.then(u'I validate labels in recipe from file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    labels_df = pd.read_csv(file_path)
    labels_tolist = labels_df["dataloop label"].to_list()[0].split(".")
    context.dataset = context.project.datasets.get(dataset_name=context.dataset.name)
    dataset_label_list = []
    for label in context.dataset.labels:
        dataset_label_list.append(label.display_label)
        while not label.children == []:
            labels = label.children
            for label in labels:
                dataset_label_list.append(label.display_label)

    assert dataset_label_list == labels_tolist, "TEST FAILED: \nDataset labels {}\nLabels uploaded {}".format(dataset_label_list, labels_tolist)
