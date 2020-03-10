Tasks and Assignments
=======================

Basic task operations:
-----------------------
Create a task:

.. code-block:: python

    project = dl.projects.get('My Project')
    dataset = project.datasets.get('My Dataset')
    filters = dl.Filters(field='dir', values='/dir1')
    task = dataset.tasks.create(task_name='task_name')

Get/list tasks:

.. code-block:: python

    import dtlpy as dl

    # get by id
    task = dl.tasks.get(task_id='5e416dfe3f71119f3a95d053')

    # get by name - in project
    project = dl.projects.get('My Project')
    task = project.tasks.get(task_name='task_name')

    # get by name - in dataset
    dataset = project.datasets.get('My Dataset')
    task = project.tasks.get(task_name='task_name')

    # list - in project
    tasks = project.tasks.list()

    # list - in dataset
    tasks = dataset.tasks.list()

Get tasks items:

.. code-block:: python

    task_items = task.get_items()

Remove items from task:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir1')
    task.remove_items(filters=filters)

Add items to task:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir1')
    task.add_items(filters=filters)

Add an assignment:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir2')
    assignment = task.create_assignment(name='assignment_name',
                                    assignee='rachel@dataloop.ai',
                                    filters=dl.Filters())

Basic assignment operations:
-----------------------------

Get/list assignments:

.. code-block:: python

    import dtlpy as dl

    # get by id
    assignment = dl.assignments.get(assignment_id='5e416dfe3f71119f3a95d053')

    # get by name - in project
    project = dl.projects.get('My Project')
    assignment = project.assignments.get(assignment_name='assignment_name')

    # get by name - in dataset
    dataset = project.datasets.get('My Dataset')
    assignment = dataset.assignments.get(assignment_name='assignment_name')

    # get by name - in task
    task = project.tasks.get(task_name='task_name')
    assignment = task.assignments.get(assignment_name='assignment_name')

    # list - in project
    assignments = project.assignments.list()

    # list - in dataset
    assignments = dataset.assignments.list()

    # list - in task
    assignments = task.assignments.list()

Get assignments items:

.. code-block:: python

    assignment_items = assignment.get_items()

Remove items from assignment:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir1')
    assignment.remove_items(filters=filters)

Add items to assignment:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir1')
    assignment.add_items(filters=filters)

Create assignment:

.. code-block:: python

    filters = dl.Filters(field='dir', values='/dir1')
    dl.assignments.create(assignment_name='name',
                           annotator='chandler',
                           dataset=dataset,
                           project_id=project.id,
                           filters=filters)

Creating a task with assignments:
----------------------------------

.. code-block:: python

    project = dl.projects.get('My Project')
    dataset = project.datasets.get('My Dataset')
    filters = dl.Filters(field='dir', values='/dir1')
    task = dataset.tasks.create(task_name='task_name',
                                assignees=['ross@dataloop.ai', 'monica@dataloop.ai', 'joey@dataloop.ai'],
                                filters=filters)

This will create a task for items that match the filter and create 3 assignments.
The items will be divided equally between assignments.
