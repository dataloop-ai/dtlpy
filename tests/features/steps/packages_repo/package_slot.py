import behave


@behave.when(u'I add UI slot to the package')
def step_impl(context):

    context.filters = context.dl.Filters()
    context.slot = context.dl.PackageSlot(module_name='default_module',
                          function_name='run',
                          display_name="ui_slot",
                          display_icon='fas fa-play',
                          post_action=context.dl.SlotPostAction(
                              type=context.dl.SlotPostActionType.NO_ACTION),
                          display_scopes=[
                              context.dl.SlotDisplayScope(
                                  filters=context.filters,
                                  resource=context.dl.SlotDisplayScopeResource.ITEM,
                                  panel=context.dl.UI_BINDING_PANEL_ALL)
                          ])

    context.package.slots = []
    context.package.slots.append(context.slot)
    context.package = context.package.update()


@behave.then(u'I validate slot is added to the package')
def step_impl(context):
    assert context.package.slots != [], "No slots added to the package"
    assert context.package.slots[0].to_json() == context.slot.to_json(), "The slot in the package is not equal to uploaded slot ###package###\n {}\n###uploaded-Slot###\n{}".\
        format(context.package.slots[0].to_json(), context.slot.to_json())
