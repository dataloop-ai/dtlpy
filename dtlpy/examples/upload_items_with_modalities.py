def main(project_name, dataset_name):
    import traceback
    import random
    import string
    import dtlpy as dl
    from concurrent.futures import ThreadPoolExecutor

    def upload_single(w_url, w_metadata):
        try:
            item = dataset.items.upload(local_path=dl.UrlLink(
                ref=w_url,
                name='.{}.json'.format(
                    ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)))),
                remote_path='/cats',
                item_metadata=w_metadata)
            return item.id
        except:
            print(traceback.format_exc())
            return None

    primary_url = 'https://images.unsplash.com/photo-1518020382113-a7e8fc38eac9'
    secondary_urls = [
        'https://images.unsplash.com/photo-1543852786-1cf6624b9987',
        'https://images.unsplash.com/photo-1561948955-570b270e7c36'
    ]
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)

    pool = ThreadPoolExecutor(max_workers=32)
    jobs = list()
    for i_url, url in enumerate(secondary_urls):
        jobs.append(pool.submit(upload_single, **{'w_url': url,
                                                  'w_metadata': {'user': {'num': i_url}}}))
    pool.shutdown()
    secondary_ids = [j.result() for j in jobs]
    modalities = list()
    for i_secondary_id, secondary_id in enumerate(secondary_ids):
        modalities.append(dl.Modality(modality_type=dl.ModalityTypeEnum.OVERLAY,
                                      ref=secondary_id,
                                      name='cat_num:{}'.format(i_secondary_id)).to_json())

    primary_item = dataset.items.upload(local_path=dl.UrlLink(ref=primary_url),
                                        item_metadata={'system': {'modalities': modalities}})
