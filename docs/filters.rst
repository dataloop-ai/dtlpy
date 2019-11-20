Filters
=======

Using filters you can filter out items and get a generator of the filtered items.
Filters entity help build such filter

Filters options (or any combination of them):

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# filter specific filename
	filters.add(field='filename', values='/morty.jpg')

	# filter specific entire folder
	filters.add(field='dir', values='/rick')

	# filter multiple directories
	filters.add(field='dir', values=['/rick', '/jerry'], operator='in')

	# get filtered items:
	pages = dataset.items.list(filters=filters)

Hidden items and directories

By default filters ignore hidden items

and directories

If you want to change this behaviour:


.. code-block:: python

    # create a filters instance
	filters = Filters()
    filters.show_hidden = True
    filters.show_dirs = True

More filters options:

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# filter by metadata field
	filters.add(field='metadata.user.some_filed', values=True)

	# filter by annotated items
	filters.add(field='annotated', values=True)

	# filter by date created
	# (gt = greater than...)
	filters.add(field='createdAt', values='01/06/2019', operator='gt')


Get annotations using filters:

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# set resource
	filters.resource = 'annotations'

	# add filter
	filters.add(field='label', values='dog')


Filter items by their annotations:

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# filter by item name
	# (only items with the string "pets" anywhere in their name)
	filters.add(field='name', values='*pets*', operator='glob')

	# filter by item's annotations
	# (only items with annotations labeled "cat")
	filters.add_join(field='label', values='cat')


Filters method:

Filters default method is performing 'AND' between all filters

This behavior can be changed:

.. code-block:: python

	# create a filters instance
	filters = Filters()

    # get all items created before or after 2018
    filters.add(field='createdAt', values='01/01/2018', operator='gt')
    filters.add(field='createdAt', values='01/01/2019', operator='lt')

    # change method to OR
    filters.method = 'or'

When adding a filter, you have some operators available to use:

glob -> string global expressions such as !, *, **

eq -> equal

ne -> not equal

gt -> greater than

lt -> less than

in -> is in a list (when using this expression values should be a list)

Update user metadata with filters:
update_value must be a dictionary.
The dictionary will update only user metadata.

.. code-block:: python

    #########################
    # update filtered items #
    #########################
    # to add filed annotatedDogs to all filtered items and give value True
    # this field will be added to user metadata
    update_values = {'annotatedDogs': True}

    # update
    pages = dataset.items.update(filters=filters, update_values=update_values)


If before update metadata was:

.. code-block:: python

    {'system': {...},
    'user':{
    'plugins': {...},
    'annotation_notes': [...]
    }}

Then, after update it will be:

.. code-block:: python

    {'system': {...},
    'user':{
    'plugins': {...},
    'annotation_notes': [...],
    'annotatedDogs': True
    }}

More advanced filtering options
################################
If you want filter items/annotations by "or" and "and" options you can do so by specifying which filters will be check
 with "or" and which ones with "and":

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# filters with or
	filters.add(field='name', values='*dogs*', operator='glob', method="or")
	filters.add(field='name', values='*cats*', operator='glob', method="or")

    # filters with and
	filters.add(field='annotated', values=True, method='and)
	filters.add(field='metadata.user.is_automated', values=True, method='and)

I the above example, we want to get items that are annotated AND have field "is_automated=True" in their metadata.
Those items should alse have either the string "dogs" or "cats" in their name.


You can also create your own custom filter dictionary and use it instead:.
For the above example, the filter will look something like that:

.. code-block:: python

	{'$or': [{'name': {'$glob': '*dogs*'}},
             {'name': {'$glob': '*cats*'}}],
     '$and': [{'annotated': True},
              {'metadata.user.is_automated': True},
              {'hidden': False},
              {'type': 'file'}]}
