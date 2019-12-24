def main():
    import dtlpy as dl
    dl.setenv('dev')

    ########
    # prep #
    ########
    project = dl.projects.get(project_name='RQL')
    dataset = project.datasets.get(dataset_name='Dataset')

    #################
    ###   Items   ###
    #################

    ##################
    # create filters #
    ##################
    filters = dl.Filters()
    # set resource
    filters.resource = 'items'
    # add filter - only files
    filters.add(field='type', values='file')
    # add filter - only annotated items
    filters.add(field='annotated', values=True)
    # add filter - filename includes 'dog'
    filters.add(field='filename', values='*dog*')
    # add filter - created since June 2019
    # -- time filters -- must be in ISO format and in UTC (offset from local time). converting using datetime package as follows:
    import datetime, time
    timestamp = datetime.datetime(year=2019, month=10, day=27, hour=15, minute=39, second=6,
                                  tzinfo=datetime.timezone(datetime.timedelta(seconds=-time.timezone))).isoformat()
    filters.add(field='createdAt', values=timestamp, operator='gt')

    ######################
    # get filtered items #
    ######################
    # return results sorted by ascending id 
    filters.sort_by(field='filename')
    pages = dataset.items.list(filters=filters)

    #########################
    # update filtered items #
    #########################
    # to add filed annotatedDogs to all filtered items and give value True
    # this field will be added to user metadata
    # create update order
    update_values = {'annotatedDogsSingJune2019': True}

    # update
    pages = dataset.items.update(filters=filters, update_values=update_values)

    # #########################
    # # delete filtered items #
    # #########################
    # dataset.items.delete(filters=filters)

    #####################################
    # filter items by their annotations #
    #####################################
    filters = dl.Filters()
    # set resource
    filters.resource = 'items'
    # add filter - only files
    filters.add(field='type', values='file')

    # add annotation filters - only items with 'box' annotations
    filters.add_join(field='type', values='box')

    # get results
    pages = dataset.items.list(filters=filters)

    #######################
    ###   Annotations   ###
    #######################

    ##################
    # create filters #
    ##################
    filters = dl.Filters()
    # set resource
    filters.resource = 'annotations'
    # add filter - only box annotations
    filters.add(field='type', values='box')
    # add filter - only dogs
    filters.add(field='label', values=['Dog', 'cat'], operator='in')
    # add filter - annotated by Joe and David
    filters.add(field='creator', values=['Joe@dataloop.ai', 'David@dataloop.ai', 'oa-test-1@dataloop.ai'], operator='in')

    ############################
    # get filtered annotations #
    ############################
    # return results sorted by descending id 
    filters.sort_by(field='id', value='descending')
    pages = dataset.items.list(filters=filters)

    ###############################
    # update filtered annotations #
    ###############################
    # to add filed annotation_quality to all filtered annotations and give them value 'high'
    # this field will be added to user metadata
    # create update order
    update_values = {'annotation_quality': 'high'}

    # update
    pages = dataset.items.update(filters=filters, update_values=update_values)

    ###############################
    # delete filtered annotations #
    ###############################
    dataset.items.delete(filters=filters)


if __name__ == '__main__':
    main()
