def main():
    from dtlpy.utilities.annotations import DtlpyToVoc

    converter = DtlpyToVoc(project_name='MyProject',
                           dataset_name='MyDataset',
                           output_annotations_path='/local/path/to/save/annotations',
                           remote_path='/remote/platform/path/to/convert')
    converter.run()
