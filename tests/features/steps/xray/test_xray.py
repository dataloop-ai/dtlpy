import behave


@behave.given(u'Some initial setup')
def before_all(context):
    return None


@behave.when(u'creating foo')
def creating_foo(context):
    return None


@behave.when(u'creating bar')
def creating_bar(context):
    return None


@behave.then(u'return foo')
def return_foo(context):
    return None


@behave.then(u'return bar')
def return_bar(context):
    return None


@behave.then(u'foo')
def foo(context):
    assert True == True


@behave.given(u'existing foo')
def existing_foo(context):
    return None
