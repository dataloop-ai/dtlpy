import os
import io
import behave


@behave.when(u'I get assignment items')
def step_impl(context):
    context.assignment_items = context.assignment.get_items()


@behave.then(u'I receive a list of "{count}" assignment items')
def step_impl(context, count):
    assert context.assignment_items.items_count == int(count)




