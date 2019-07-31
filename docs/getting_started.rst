Getting Started
===============

*dtlpy* enables python connection to Dataloop's environment
dtlpy package provides two interfaces: python SDK and CLI tool. The common use cases :
Python SDK: If you wish to automate data ops directly from your code.
CLI(Command line interface): Usually used for uploading or downloading data in a more fault tolerant way comapred to browser.

Login
-----
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
You can create a generator of items with different filters

.. code-block:: python

	# Get the project
	project = dl.projects.get(project_name='MyProject')
	# Get the dataset
	dataset = project.datasets.get(dataset_name='MyDataset')
	# Get items in pages (100 item per page)
	filters = dl.Filters()
	filters.add(field='filename', values='/winter/is/coming/*')
	pages = dataset.items.list(filters=filters)
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
	dataset.items.upload(
		local_path=r'C:\home\dogs', #  can be a directory
		remote_path='/images/dogs',
		overwrite=False
	)

	# Upload entire folder to dataset dataset with annotations
	dataset.items.upload(
		local_path=r'C:\home\images\dogs', # folder of images
		local_annotations_path=r'C:\home\json\dogs', # dataloop annotations files (jsons)
		remote_path='/images/dogs',
		overwrite=False
	)

	# Upload single image
	dataset.items.upload(
		local_path='/images/000000000036.jpg', # can be a filepath
		remote_path='/dog'
	)

	# if uploading a buffer - you can set the name of the uploaded file
	filters = dl.Filters()
	filters.add(field='filename', values='/winter/is/coming/arya.jpg')
	buffer = dataset.items.download(filters=filters, save_locally=False)
	buffer.name = 'arya_stark.jpg'
	dataset.items.upload(
		local_path=buffer, # can be a filepath
		remote_path='/with_last_name'
	)

	# Download entire directory with json annotations files
	filters = dl.Filters()
	filters.add(field='filename', values='/winter/is/coming/**')
	filenames = dataset.items.download(
	    filters=filters,
		local_path='/home/images',
		overwrite=True,
		annotation_options=['json'] # download with annotations
	)

Move item between folders
-------------------------
.. code-block:: python

	# get an item from location
	item = dataset.items.get(filepath='/moon/1.jpg')
	item.move('/moon/front')
	# or rename
	item.move('/moon/front/2.jpg')

More...
-------

For more examples go to :doc:`examples`.
