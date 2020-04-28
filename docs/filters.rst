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
	filters.add(field='dir', values=['/rick', '/jerry'], operator=dl.FiltersOperations.IN)

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
	import datetime, time
    timestamp = datetime.datetime(year=2019, month=10, day=27, hour=15, minute=39, second=6,
                                  tzinfo=datetime.timezone(datetime.timedelta(seconds=-time.timezone))).isoformat()
	filters.add(field='createdAt', values=timestamp, operator=dl.FiltersOperations.GREATER_THAN)


Get annotations using filters:

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# set resource
	filters.resource = dl.FiltersResource.ANNOTATION

	# add filter
	filters.add(field='label', values='dog')


Filter items by their annotations:

.. code-block:: python

	# create a filters instance
	filters = Filters()

	# filter by item name
	# (only items in dir pets)
	filters.add(field='dir', values='/pets')

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
    import datetime, time
    earlier_timestamp = datetime.datetime(year=2018, month=1, day=1, hour=0, minute=0, second=0,
                                  tzinfo=datetime.timezone(datetime.timedelta(seconds=-time.timezone))).isoformat()

    later_timestamp = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0,
                                  tzinfo=datetime.timezone(datetime.timedelta(seconds=-time.timezone))).isoformat()

    filters.add(field='createdAt', values=earlier_timestamp, operator=dl.FiltersOperations.GREATER_THAN)
    filters.add(field='createdAt', values=later_timestamp, operator=dl.FiltersOperations.LESS_THAN)

    # change method to OR
    filters.method = dl.FiltersMethod.OR

When adding a filter, you have some operators available to use:

eq -> equal
(or dl.FiltersOperation..EQUAL)

ne -> not equal
(or dl.FiltersOperation.NOT_EQUAL)

gt -> greater than
(or dl.FiltersOperation.GREATER_THAN)

lt -> less than
(or dl.FiltersOperation.LESS_THAN)

in -> is in a list (when using this expression values should be a list)
(or dl.FiltersOperation.IN)

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
	filters.add(field='dir', values='/dogs', method=dl.FiltersMethod.OR)
	filters.add(field='dir', values='/cats', method=dl.FiltersMethod.OR)

    # filters with and
	filters.add(field='annotated', values=True, method=dl.FiltersMethod.AND)
	filters.add(field='metadata.user.is_automated', values=True, method=dl.FiltersMethod.AND)

I the above example, we want to get items that are annotated AND have field "is_automated=True" in their metadata.
Those items should alse have either the string "dogs" or "cats" in their name.


You can also create your own custom filter dictionary and use it instead:.
For the above example, the filter will look something like that:

.. code-block:: python

	{'$or': [{'dir': '/dogs'},
             {'dir': '/cats'}],
     '$and': [{'annotated': True},
              {'metadata.user.is_automated': True},
              {'hidden': False},
              {'type': 'file'}]}
