Getting Started
===============

*dtlpy* enables python connection to Dataloop's environment

Login
--------------------------
.. code-block:: python

	from dtlpy import PlatformInterface
	# init 
	dlp = PlatformInterface()
	# login 
	dlp.login()
	# print projects
	dlp.projects.list().print()
	
Create project and dataset
--------------------------
.. code-block:: python

	project = dlp.projects.create(project_name='MyProject')

	dataset = project.datasets.create(dataset_name='MyDataset',
									  classes={'pinky': (255, 0, 0), 'the brain': (0, 0, 255)})

Delete project and dataset
--------------------------
.. code-block:: python

	result = project.datasets.delete(dataset_name='MyDataset')

	dlp.projects.delete(project_name='MyProject')

List projects, datasets
-----------------------
.. code-block:: python

	# list projects
	projects = dlp.projects.list().print()

	project = dlp.projects.get(project_name='MyProject')
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

	dataset = dlp.projects.get(project_name='MyProject').datasets.get(dataset_name='MyDataset')
	pages = dataset.items.list()
	
	for page in pages:
		for item in page:
			print(item.name)

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
	filenames = project.datasets.download(
		dataset_name='MyDataset',
		local_path='/home/images',
		download_options='merge'
	)
	# upload video
	Videos.split_and_upload(
		filepath='/home/videos/messi.mp4',
		project_name='MyProject',
		dataset_name='MyDataset',
		split_pairs=[(0, 5), (10, 20)],
		remote_path='/'
	)

More...
-------

For more examples go to :doc:`examples`.