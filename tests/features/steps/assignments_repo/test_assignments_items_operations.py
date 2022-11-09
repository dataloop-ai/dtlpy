import os
import io
import behave


@behave.when(u'I get assignment items')
def step_impl(context):
    context.assignment_items = context.assignment.get_items()


@behave.then(u'I receive a list of "{count}" assignment items')
def step_impl(context, count):
    assert context.assignment_items.items_count == int(count)


@behave.then(u'I receive a list of "{count}" items for each assignment')
def step_impl(context, count):
    for assignment in context.task.assignments.list():
        assert assignment.total_items == int(count), "TEST FAILED: Assignment items expected : {} , Got : {}".format(count, assignment.total_items)




