import behave


@behave.then(u'I will see the on the note annotations the following messages')
def step_impl(context):
    context.messages = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "messages":
            context.messages = eval(parameter.cells[1])

    if context.messages is not None:
        for message_index in range(len(context.messages)):
            assert context.messages[message_index] == context.annotation.messages[message_index].body
