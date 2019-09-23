def main():
    import dtlpy as dl

    project = dl.projects.get(project_name='Ocean')
    dataset = project.datasets.get(dataset_name='Sharks')

    converter = dl.Converter()
    converter.convert_dataset(dataset=dataset, to_format='voc',
                              local_path='home/voc_annotations/sharks')
