import behave
import dictdiffer


@behave.when(u"I get package entity from service")
def step_impl(context):
    context.package = context.service.package


@behave.when(u"I activate UI slot in service")
def step_impl(context):
    context.service.activate_slots(project_id=context.project.id)


@behave.when(u'I update UI slot display_name to "{display_name}"')
def step_impl(context, display_name):
    assert len(context.package.slots) == 1, "TEST FAILED: Expected to get 1 UI slot , Actual got : {}".format(len(context.package.slots))

    context.package.slots[0].display_name = display_name
    context.package = context.package.update()


@behave.then(u'I validate service UI slot is equal to settings')
def step_impl(context):
    dict_1 = context.package.slots[0].to_json()
    dict_2 = context.setting_get.metadata['slots'][0]

    assert [] == list(dictdiffer.diff(dict_1, dict_2)), "TEST FAILED: Different in service slot and settings.\n{}".format(list(dictdiffer.diff(dict_1, dict_2)))

