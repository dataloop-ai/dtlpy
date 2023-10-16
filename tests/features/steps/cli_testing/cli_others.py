import behave


@behave.then(u'Version is correct')
def step_impl(context):
    output = context.out.decode('utf-8')
    assert context.dl.__version__ in output, f"Version {context.dl.__version__} is not correct in output {output}"


@behave.then(u'"{msg}" in output')
def step_impl(context, msg):
    msg = msg.replace('<random>', context.random)
    output = context.out.decode('utf-8')
    assert msg.lower() in output.lower()
