def main():
    import dtlpy as dl

    project = dl.projects.get(project_name='project_name')

    ##################
    # create trigger #
    ##################
    # create Item trigger
    # that will trigger service with given id
    # when item is created
    trigger = project.triggers.create(service_ids=['some_service_id'],
                                      resource=dl.FiltersResource.ITEM,
                                      actions=dl.TriggerAction.CREATED,
                                      active=True)

    # create Annotation trigger
    # that will trigger service with given id
    # when Annotation is deleted
    trigger = project.triggers.create(service_ids=['some_service_id'],
                                      resource=dl.FiltersResource.ANNOTATION,
                                      actions=dl.TriggerAction.DELETED,
                                      active=True)

    ##################
    # update trigger #
    ##################
    # if we want trigger to be triggered on Created
    trigger.actions = ['Annotation']
    trigger.update()

    # update trigger filters
    # to work only on specific items
    # trigger will be triggered only on
    # items with string: dog in their name
    filters = dl.Filters()
    filters.add(field='filename', values='*dog*')
    trigger.filters = filters
    trigger.update()

    ##################
    # delete trigger #
    ##################
    trigger.delete()

    ############################
    # list of project triggers #
    ############################
    project.triggers.list()
