import behave
import dtlpy as dl
import random
import sys
import time


@behave.given('I create "{entity}" name "{name}"')
@behave.when('I create "{entity}" name "{name}"')
def step_impl(context, entity, name):
    """
    :param context:
    :param entity: org / project / dataset
    :param name: object name
    :return:
    """
    # add random to name
    context.num = time.time()
    context.name = f'to-delete-test-{name}_{int(context.num)}'

    if entity == "org":
        success, response = dl.client_api.gen_request(req_type='post',
                                                      path='/orgs',
                                                      json_req={"name": context.name}
                                                      )

        context.org = dl.entities.Organization.from_json(client_api=dl.client_api,
                                                         _json=response.json())

        assert isinstance(context.org, context.dl.entities.Organization)

        context.feature.dataloop_feature_org = context.org

        if not success:
            raise context.dl.exceptions.PlatformException(response)

    elif entity == "project":

        context.project = dl.projects.create(project_name=context.name)

        assert isinstance(context.project, context.dl.entities.Project)

        context.feature.dataloop_feature_project = context.project

    elif entity == "dataset":

        context.dataset = context.project.datasets.create(dataset_name=context.name)

    else:
        sys.exit("You must specify object as either 'org' 'project' 'dataset'")
