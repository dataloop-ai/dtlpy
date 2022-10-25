import behave
import requests


@behave.then(u'I validate the platform url "{platform_url}" works')
def step_impl(context, platform_url):
    urls_list = {
        "project.platform_url": context.dl.projects.get(project_id=context.project.id),
        "dataset.platform_url": context.dl.datasets.get(dataset_id=context.dataset.id),
        "project.dataset.platform_url": context.project.datasets.get(dataset_id=context.dataset.id),
        "item.platform_url": context.dl.items.get(item_id=context.item.id),
        "dataset.item.platform_url": context.dataset.items.get(item_id=context.item.id),
        "project.dataset.item.platform_url": context.project.datasets.get(dataset_id=context.dataset.id).items.get(item_id=context.item.id),
    }

    output_url = urls_list[platform_url].platform_url
    request_code = requests.get(url=output_url).status_code
    assert request_code == 200
