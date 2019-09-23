def main():
    import dtlpy as dl
    
    project = dl.projects.get(project_name='Jungle')
    dataset = project.datasets.get(dataset_name='Tigers')

    converter = dl.Converter()
    converter.convert_dataset(dataset=dataset, to_format='yolo',
                              local_path='home/yolo_annotations/tigers')
