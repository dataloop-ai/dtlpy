import behave


@behave.when(u'I delete driver by the name "{driver_name}"')
def step_impl(context, driver_name):
    try:
        context.project.drivers.delete(driver_name=driver_name, sure=True, really=True)
        context.to_delete_drivers_ids.pop()
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I validate driver "{driver_name}" not longer in project drivers')
def step_impl(context, driver_name):
    assert driver_name not in [driver.name for driver in context.project.drivers.list()], "TEST FAILED: Driver: {} found in project drivers list".format(driver_name)
