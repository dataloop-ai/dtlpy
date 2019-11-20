
####################
Links
####################

Links are items that do not have their own binaries, instead, they have links to binaries from
other items or URL links.

Before we get started with Links:

.. code-block:: python

    import dtlpy as dl

    project = dl.projects.get(project_name='my project')

Item Links
##############

Items that reflects other items' binaries.

If I want to make links from one dataset to another

Lets say I have 2 datasets:

.. code-block:: python

    # First dataset
    first_dataset = project.datasets.get(dataset_name='first dataset')

    # Second dataset
    second_dataset = project.datasets.get(dataset_name='second dataset')


Upload Single link

.. code-block:: python

    # Get Item
    item = first_dataset.items.get(filepath='blue_dog.jpg')

    # Create link
    link = dl.ItemLink(item=item)

    # Upload link
    second_dataset.items.upload(local_path=link, remote_path='/dogs')

Upload multiple links

.. code-block:: python

    # get items
    filters = dl.Filters()
    filters.add(field='dir', values='/')
    pages = first_dataset.items.list(filters=filters)

    # create links
    links = list()
    for page in pages:
        links.append(dl.ItemLink.from_list(items=page.items))

    # Upload links
    second_dataset.items.upload(local_path=links)

URL Links
##############

Items that reflects binaries from a URL.

Lets say I have a dataset:

.. code-block:: python

    dataset = project.datasets.get(dataset_name='My dataset')

Upload a single link

.. code-block:: python

    # url
    url_path = 'http://ww.somw_website/beutiful_flower.jpg'

    # Create link
    link = dl.UrlLink(ref=url_path)

    # Upload link
    dataset.items.upload(local_path=link)

Upload multiple links

.. code-block:: python

    # Given I have a list of url's
    url_list = list()

    # Create link list
    links = dl.UrlLink.from_list(url_list=url_list)

    # Upload links
    dataset.items.upload(local_path=links)


