Getting Started
===============

*dtlpy* enables python connection to Dataloop's environment
dtlpy package provides two interfaces: python SDK and CLI tool. The common use cases :
Python SDK: If you wish to automate data ops directly from your code.
CLI(Command line interface): Usually used for uploading or downloading data in a more fault tolerant way comapred to browser.

Login
--------------------------
.. code-block:: python

	# import dtlpy
	import dtlpy as dl
	# login
	dl.login()
	# print projects
	dl.projects.list().print()

Create project and dataset
--------------------------
.. code-block:: python

	project = dl.projects.create(project_name='MyProject')

	dataset = project.datasets.create(dataset_name='MyDataset', 
					labels={'pinky': (255, 0, 0), 'the brain': (0, 0, 255)})

List projects, datasets
-----------------------
.. code-block:: python

	# list projects
	projects = dl.projects.list()
	projects.print()

	project = dl.projects.get(project_name='MyProject')
	project.print()

	# list dataset
	datasets = project.datasets.list()
	datasets.print()

	dataset = project.datasets.get(dataset_name='MyDataset')
	dataset.print()

Iterator of items
-----------------
You can create a generator of items with different queries

.. code-block:: python

	dataset = dl.projects.get(project_name='MyProject').datasets.get(dataset_name='MyDataset')
	pages = dataset.items.list()

	for page in pages:
		for item in page:
			item.print()

Upload and download items
-------------------------
.. code-block:: python

	# upload SINGLE image
	dataset.items.upload(
		filepath='/images/000000000036.jpg',
		remote_path='/dog'
	)

	# upload dataset (folder of images)
	filename = project.datasets.upload(
		dataset_name='MyDataset',
		local_path='/home/images',
		upload_options='overwrite'
	)

	# download dataset
	filenames = dataset.download(
		dataset_name='MyDataset',
		local_path='/home/images',
		download_options={'overwrite': True, 'relative_path': True}
	)

More...
-------

For more examples go to :doc:`examples`.
