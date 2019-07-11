Filters
=======

Using filters you can filter out items and get a generator of the filtered items.
Filters entity help build such filter

Filters options (or any combination of them):

.. code-block:: python

	# create a filters instance
	filters = Filters()
	# filter only items
    filters.add(field='type', values='file')
	# filter specific filename
	filters.add(field='filename', values='/morty.jpg')
	# filter specific entire folder
	filters.add(field='filename', values='/rick/*')

	# filter multiple directories
	filters = Filters()
	filters.add(field='filename', values='/rick/*')
	filters.add(field='filename', values='/jerry/*')
	filters.method = 'or'


