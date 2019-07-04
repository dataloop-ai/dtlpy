Filters
=======

Using filters you can filter out items and get a generator of the filtered items.
Filters entity help build such filter

Filters options (or any combination of them):

.. code-block:: python

	# create a filters instance
	filters = Filters()
	# filter only items
	filters(field='type', value='file')
	# filter specific filename
	filters(field='filename', value='/morty.jpg')
	# filter specific entire folder
	filters(field='filename', value='/rick/*')

	# filter multiple directories
	filters(field='filename', value='/rick/*', operator='or')
	filters(field='filename', value='/jerry/*', operator='or')

