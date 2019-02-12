def main():
    """
    Add any metadata to item
    :return:
    """
    from dtlpy.platform_interface import PlatformInterface

    dlp = PlatformInterface()

    dataset = dlp.projects.get('ImageNet').datasets.get(dataset_name='sample')

    item = dataset.items.get(filename='/000000001036.jpg')

    metadata = item.metadata
    metadata['user']['MyKey'] = 'MyVal'
    item.metadata = metadata

    dataset.items.edit(item=item, system_metadata=True)
