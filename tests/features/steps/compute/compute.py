import datetime
import json
import os
import random
import string
import time
import dtlpy as dl
import behave
from behave import given, when, then


def random_5_chars():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'


@behave.given(u'I create a compute')
def step_impl(context):
    devops_output = {
        "authentication": {
            "ca": os.environ.get('COMPUTE_CLUSTER_CA'),
            "token": os.environ.get('COMPUTE_CLUSTER_TOKEN')
        },
        "config": {
            "endpoint": os.environ.get('COMPUTE_CLUSTER_ENDPOINT'),
            "kubernetesVersion": "1.29",
            "name": "rc-faas-eks",
            "nodePools": [
                {
                    "deploymentResources": {
                        "cpu": 2,
                        "gpu": 1,
                        "memory": 6
                    },
                    "dlTypes": [
                        "gpu-t4-s"
                    ],
                    "name": "gpu16-np",
                    "nodeSelector": {
                        "dl-type": "gpu-t4-snp"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "gpu-t4-snp"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "sku",
                            "operator": "Equal",
                            "value": "gpu"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 2,
                        "gpu": 1,
                        "memory": 6
                    },
                    "dlTypes": [
                        "gpu-t4-s"
                    ],
                    "name": "gpu16-p",
                    "nodeSelector": {
                        "dl-type": "gpu-t4-sp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "gpu-t4-sp"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "sku",
                            "operator": "Equal",
                            "value": "gpu"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 4,
                        "gpu": 1,
                        "memory": 16
                    },
                    "dlTypes": [
                        "gpu-t4-m"
                    ],
                    "name": "gpu32-np",
                    "nodeSelector": {
                        "dl-type": "gpu-t4-mnp"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "gpu-t4-mnp"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "sku",
                            "operator": "Equal",
                            "value": "gpu"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 4,
                        "gpu": 1,
                        "memory": 16
                    },
                    "dlTypes": [
                        "gpu-t4-m"
                    ],
                    "name": "gpu32-p",
                    "nodeSelector": {
                        "dl-type": "gpu-t4-mp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "gpu-t4-mp"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "sku",
                            "operator": "Equal",
                            "value": "gpu"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-l"
                    ],
                    "name": "highmem_l_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-l-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-l-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-l"
                    ],
                    "name": "highmem_lp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-l"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-l"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-m"
                    ],
                    "name": "highmem_m_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-m-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-m-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-m"
                    ],
                    "name": "highmem_mp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-mp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-mp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-s"
                    ],
                    "name": "highmem_s_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-s-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-s-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-s"
                    ],
                    "name": "highmem_sp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-sp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-sp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-xs"
                    ],
                    "name": "highmem_xs_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-xs-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-xs-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "highmem-xs"
                    ],
                    "name": "highmem_xsp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "highmem-xsp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "highmem-xsp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 2,
                        "memory": 6
                    },
                    "dlTypes": None,
                    "name": "monitoring",
                    "nodeSelector": {
                        "component": "monitoring"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "component",
                            "operator": "Equal",
                            "value": "monitoring"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-l"
                    ],
                    "name": "regular_l_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-l-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-l-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-l"
                    ],
                    "name": "regular_lp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-lp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-lp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-m"
                    ],
                    "name": "regular_m_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-m-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-m-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-m"
                    ],
                    "name": "regular_mp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-mp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-mp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-s"
                    ],
                    "name": "regular_s_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-s-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-s-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-s"
                    ],
                    "name": "regular_sp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-sp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "true"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-sp"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-xs"
                    ],
                    "name": "regular_xs_np",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-xs-np"
                    },
                    "preemtible": False,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-xs-np"
                        }
                    ]
                },
                {
                    "deploymentResources": {
                        "cpu": 1,
                        "memory": 1
                    },
                    "dlTypes": [
                        "regular-xs"
                    ],
                    "name": "regular_xsp",
                    "nodeSelector": {
                        "dl-type": "no-gpu-regular",
                        "size": "regular-xsp"
                    },
                    "preemtible": True,
                    "tolerations": [
                        {
                            "effect": "NoSchedule",
                            "key": "node-pool",
                            "operator": "Equal",
                            "value": "dataloop"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "preemptible",
                            "operator": "Equal",
                            "value": "false"
                        },
                        {
                            "effect": "NoSchedule",
                            "key": "size",
                            "operator": "Equal",
                            "value": "regular-xsp"
                        }
                    ]
                }
            ],
            "provider": dl.ClusterProvider.AWS
        }
    }
    integration_name = 'cluster_integration_test_' + datetime.datetime.now().isoformat().split('.')[0].replace(':', '_')
    context.integration = context.project.integrations.create(
        integrations_type=dl.IntegrationType.KEY_VALUE,
        name=integration_name,
        options={
            'key': integration_name,
            'value': json.dumps(devops_output['authentication'])
        })
    context.feature.to_delete_integrations_ids.append(context.integration.id)
    context.feature.dataloop_feature_integration = context.integration
    compute_context = dl.ComputeContext([], context.project.org['id'], context.project.id)
    node_pools = [dl.NodePool.from_json(n) for n in devops_output['config']['nodePools']]

    cluster = dl.ComputeCluster(devops_output['config']['name'],
                                devops_output['config']['endpoint'],
                                devops_output['config']['kubernetesVersion'],
                                devops_output['config']['provider'],
                                node_pools,
                                {},
                                dl.Authentication(dl.AuthenticationIntegration(context.integration.id,
                                                                               context.integration.type)))
    context.compute = dl.computes.create(devops_output['config']['name'], compute_context, [], cluster, dl.ComputeType.KUBERNETES)
    context.feature.dataloop_feature_compute = context.compute


@behave.when(u'i set driver feaureflag')
def step_impl(context):
    settings=dl.settings.list(filters=dl.Filters(resource= dl.FiltersResource.SETTINGS, custom_filter={
        "name":"defaultFaaSDriverId", "scope.id": context.project.org['id'] })).items
    if not settings or len(settings) == 0:
        context.setting = dl.settings.create(
            setting=dl.Setting(
                value=context.compute.name,
                name='defaultFaaSDriverId',
                value_type=dl.SettingsValueTypes.STRING,
                scope=dl.SettingScope(
                    type=dl.PlatformEntityType.ORG,
                    id=context.project.org['id'],
                    role=dl.Role.ALL,
                    prevent_override=False,
                    visible=True,
                ),
                section_name=dl.SettingsSectionNames.APPLICATIONS
            )
        )
    else:
        context.setting = dl.settings.update(
            setting=dl.Setting(
                id=settings[0].id,
                value=context.compute.name,
                name='defaultFaaSDriverId',
                value_type=dl.SettingsValueTypes.STRING,
                scope=dl.SettingScope(
                    type=dl.PlatformEntityType.ORG,
                    id=context.project.org['id'],
                    role=dl.Role.ALL,
                    prevent_override=False,
                    visible=True,
                ),
                section_name=dl.SettingsSectionNames.APPLICATIONS
            )
        )


@given(u'There are 2 drivers')
def step_impl(context):
    context.default_driver = os.environ.get('DEFAULT_DRIVER', 'azure-plugins-rc')
    context.secondary_driver = os.environ.get('SECOND_DRIVER', 'plugins-rc')


@given(u'New Organization')
def step_impl(context):
    env = context.dl.client_api.environment[dl.client_api.environment.index('//')+2:context.dl.client_api.environment.index('-')]
    key = 'ORG_ID_' + env.upper()
    org_id = os.environ.get(key, '2e8370da-c559-433d-93a3-4e7922a9b524')
    context.org = context.dl.organizations.get(organization_id=org_id)
    # success, response = context.dl.client_api.gen_request(
    #     req_type='post',
    #     path='/orgs',
    #     json_req={'name': 'org_' + random_5_chars()}
    # )
    # org_id = response.json()['id']
    # context.org = context.dl.organizations.get(organization_id=org_id)


@given(u'Organization has a project')
def step_impl(context):
    success, response = context.dl.client_api.gen_request(
        req_type='patch',
        path='/projects/{}/org'.format(context.project.id),
        json_req={'org_id': context.org.id}
    )
    assert success, 'Failed to add project to organization'
    context.project = context.dl.projects.get(project_id=context.project.id)
    assert context.project.org['id'] == context.org.id, 'Project is not in the organization'


@given(u'Organization has no default driver')
def step_impl(context):
    try:
        setting_name = 'defaultFaaSDriverId'
        settings = context.dl.settings.resolve(org_id=context.org.id, user_email=context.dl.info()['user_email'])
        driver_settings = [s for s in settings if s.name == setting_name]
        for setting in driver_settings:
            setting.delete()
    except Exception as e:
        pass


@given(u'Services deployed in the project is not using the default driver')
def step_impl(context):
    def run(item):
        return item

    context.first_service = context.project.services.deploy(name='first-service-' + random_5_chars(), func=run)
    assert context.first_service.driver_id == context.default_driver, 'Service is not using the default driver'


@when(u'I set default driver')
def step_impl(context):
    context.dl.service_drivers.set_default(
        service_driver_id=context.secondary_driver,
        org_id=context.org.id,
        update_existing_services=True
    )


@then(u'Organization has a default driver user setting that uses secondary driver')
def step_impl(context):
    setting_name = 'defaultFaaSDriverId'
    settings = context.dl.settings.resolve(org_id=context.org.id, user_email=context.dl.info()['user_email'])
    setting = [s for s in settings if s.name == setting_name][0]
    assert setting.value == context.secondary_driver, 'Default driver is not set correctly'
    assert setting.scope.type == context.dl.PlatformEntityType.ORG, 'Default driver is not set correctly'
    assert setting.scope.id == context.org.id, 'Default driver is not set correctly'


@then(u'Services deployed in the project are using the secondary driver')
def step_impl(context):
    def run(item):
        return item

    context.second_service = context.project.services.deploy(service_name='second-service-' + random_5_chars(),
                                                             func=run)
    assert context.second_service.driver_id == context.secondary_driver, 'Service is not using the secondary driver'


@then(u'First service is also using the secondary driver')
def step_impl(context):
    timeout = time.time() + 60 * 2
    while time.time() < timeout:
        context.first_service = context.project.services.get(service_id=context.first_service.id)
        if context.first_service.driver_id == context.secondary_driver:
            break
        time.sleep(1)
    assert context.first_service.driver_id == context.secondary_driver, 'Service is not using the secondary driver'