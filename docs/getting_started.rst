Getting Started
===============

*dtlpy* enables python connection to Dataloop's environment
dtlpy package provides two interfaces: python SDK and CLI tool. The common use cases :
Python SDK: If you wish to automate data ops directly from your code.
CLI(Command line interface): Usually used for uploading or downloading data in a more fault tolerant way comapred to browser.

Login
--------------------------
.. code-block:: python

	# Import Dataloop SDK package
	import dtlpy as dl
	# Login to Dataloop platform
	dl.login()
	# Print all your projects
	dl.projects.list().print()

Create project and dataset
--------------------------
.. code-block:: python

	# Create a new project
	project = dl.projects.create(project_name='MyProject')

	# Create a new dataset in existing project
	project = dl.projects.get(project_name='MyProject')

	dataset = project.datasets.create(dataset_name='MyDataset', 
					labels={'pinky': (255, 0, 0), 'the brain': (0, 0, 255)})

List projects, datasets
-----------------------
.. code-block:: python

	# Get a list of projects
	projects = dl.projects.list()
	# Print the list
	projects.print()

	# Get a specific project by name
	project = dl.projects.get(project_name='MyProject')
	# Print the project's properties
	project.print()

	# Get a list all datasets in the project
	datasets = project.datasets.list()
	# Print the list with all the properties
	datasets.print()

	# Get a specific dataset by name
	dataset = project.datasets.get(dataset_name='MyDataset')
	# Print the dataset's properties
	dataset.print()

Iterator of items
-----------------
You can create a generator of items with different queries

.. code-block:: python

	# Get the project
	project = dl.projects.get(project_name='MyProject')
	# Get the dataset
	dataset = project.datasets.get(dataset_name='MyDataset')
	# Get items in pages (100 item per page)
	pages = dataset.items.list()
	# Count the items
	print('Number of items in dataset: {}'.format(pages.items_count))
	# Go over all item and print the properties
	for page in pages:
		for item in page:
			item.print()

Upload and download items
-------------------------
.. code-block:: python

	# Upload entire folder to dataset dataset
	dataset.upload(
		local_path=r'C:\home\dogs',
		remote_path='/images/dogs',
		upload_options='overwrite'
	)

	# Upload SINGLE image
	dataset.items.upload(
		filepath='/images/000000000036.jpg',
		remote_path='/dog'
	)

	# Download entire dataset
	filenames = dataset.download(
		local_path='/home/images',
		download_options={'overwrite': True}
	)

More...
-------

For more examples go to :doc:`examples`.
