import time
import behave
import os
import tempfile
import random
import string


@behave.given(u'Service that restart once in init')
def step_impl(context):
    module_class_name = 'ServiceRunner'
    entry_point = 'main.py'
    name = 'test-single-crash'

    code_base_string = """
import dtlpy as dl


class {module_class_name}:
    def __init__(self):
        self.project = dl.projects.get(project_id='{project_id}')
        try:
            self.project.datasets.get(dataset_name='test-dataset')
        except:
            self.project.datasets.create(dataset_name='test-dataset')
            raise Exception('Only one InitError')

    def run(self, item):
        return item

    """.format(
        module_class_name=module_class_name,
        project_id=context.project.id
    )

    def get_randon_string(length=5):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

    codebase_dir = os.path.join(tempfile.gettempdir(), 'codebase', get_randon_string())
    os.makedirs(codebase_dir, exist_ok=True)
    code_base_filepath = os.path.join(codebase_dir, entry_point)

    with open(code_base_filepath, 'w') as f:
        f.write(code_base_string)

    context.package = context.project.packages.push(
        package_name='package-{}'.format(name),
        src_path=codebase_dir,
        modules=[
            context.dl.PackageModule(
                class_name=module_class_name,
                entry_point=entry_point,
                functions=[
                    context.dl.PackageFunction(
                        function_name='run',
                        inputs=[
                            context.dl.FunctionIO(name='item', type=context.dl.PackageInputType.ITEM)
                        ],
                        outputs=[
                            context.dl.FunctionIO(name='item', type=context.dl.PackageInputType.ITEM)
                        ]
                    )
                ]
            )
        ]
    )


@behave.when(u'service is deployed with num replicas > 0')
def step_impl(context):
    context.service = context.package.deploy(
        service_name='service-{}'.format(context.package.name.replace('package', 'service')),
        runtime=context.dl.KubernetesRuntime(
            autoscaler=context.dl.KubernetesRabbitmqAutoscaler(
                min_replicas=1,
                max_replicas=1
            )
        )
    )


@behave.then(u'service should stay active')
def step_impl(context):
    service = context.project.services.get(service_id=context.service.id)
    assert service.active is True
    context.execution = context.service.execute(item_id=context.item.id, project_id=context.project.id)

    timeout = 60 * 10
    interval = 5
    start = time.time()

    while time.time() - start < timeout:
        context.execution = context.project.executions.get(execution_id=context.execution.id)
        if context.execution.latest_status['status'] == context.dl.ExecutionStatus.SUCCESS:
            break
        time.sleep(interval)

    assert context.execution.latest_status['status'] == context.dl.ExecutionStatus.SUCCESS
