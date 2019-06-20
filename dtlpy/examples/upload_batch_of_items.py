def main():    
    import dtlpy as dl

    project_name='New of your project'
    dataset_name='New of your dataset'

    # get dataset
    dataset = dl.projects.get(project_name=project_name).datasets.get(dataset_name=dataset_name)

    # path to a local directory of items to upload
    dir_path = 'path'

    # remote directory to which item will be uploaded
    # if remote path given does not exist it will be created automatically when uploading
    remote_path = '/path'

    # can be 'merge' or 'overwrite'
    upload_options=None

    # upload
    dataset.upload_batch(filepaths=dir_path, remote_path=remote_path, upload_options=upload_options)