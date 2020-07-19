import os

# set var for assets
os.environ['DATALOOP_TEST_ASSETS'] = os.path.join(os.getcwd(), 'tests', 'assets')

from tests.features.steps.projects_repo import test_projects_create
from tests.features.steps.projects_repo import test_projects_list
from tests.features.steps.projects_repo import test_projects_get
from tests.features.steps.projects_repo import test_projects_delete

from tests.features.steps.project_entity import test_project_repo_methods

from tests.features.steps.datasets_repo import test_datasets_create
from tests.features.steps.datasets_repo import test_datasets_list
from tests.features.steps.datasets_repo import test_datasets_get
from tests.features.steps.datasets_repo import test_datasets_delete
from tests.features.steps.datasets_repo import test_datasets_update
from tests.features.steps.datasets_repo import test_datasets_download_annotations
from tests.features.steps.datasets_repo import test_datasets_download

from tests.features.steps.dataset_entity import test_dataset_repo_methods

from tests.features.steps.annotations_repo import test_annotations_get
from tests.features.steps.annotations_repo import test_annotations_list
from tests.features.steps.annotations_repo import test_annotations_delete
from tests.features.steps.annotations_repo import test_annotations_download
from tests.features.steps.annotations_repo import test_annotations_update
from tests.features.steps.annotations_repo import test_annotations_upload
from tests.features.steps.annotations_repo import test_annotations_show
from tests.features.steps.annotations_repo import test_annotations_draw

from tests.features.steps.annotation_entity import test_annotation_repo_methods
from tests.features.steps.annotation_entity import test_upload_annotations
from tests.features.steps.annotation_entity import test_annotation_json_to_object

from tests.features.steps.annotation_collection import test_annotation_collection

from tests.features.steps.items_repo import test_items_get
from tests.features.steps.items_repo import test_items_upload
from tests.features.steps.items_repo import test_items_list
from tests.features.steps.items_repo import test_items_update
from tests.features.steps.items_repo import test_items_set_items_entity
from tests.features.steps.items_repo import test_items_get_all_items
from tests.features.steps.items_repo import test_items_download_batch
from tests.features.steps.items_repo import test_items_upload_batch
from tests.features.steps.items_repo import test_items_upload_dataframe
from tests.features.steps.items_repo import test_items_delete
from tests.features.steps.items_repo import test_items_download

from tests.features.steps.item_entity import test_item_repo_methods

from tests.features.steps.ontologies_repo import test_ontologies_create
from tests.features.steps.ontologies_repo import test_ontologies_get
from tests.features.steps.ontologies_repo import test_ontologies_delete
from tests.features.steps.ontologies_repo import test_ontologies_update

from tests.features.steps.ontology_entity import test_ontology_repo_methods

from tests.features.steps.recipes_repo import test_recipes_create
from tests.features.steps.recipes_repo import test_recipes_update
from tests.features.steps.recipes_repo import test_recipes_delete

from tests.features.steps.codebases_repo import test_codebases_pack
from tests.features.steps.codebases_repo import test_codebases_init
from tests.features.steps.codebases_repo import test_codebases_unpack
from tests.features.steps.codebases_repo import test_codebases_get
from tests.features.steps.codebases_repo import test_codebases_list_versions
from tests.features.steps.codebases_repo import test_codebases_list

from tests.features.steps.codebase_entity import test_codebase_repo_methods

from tests.features.steps.utilities import platform_interface_steps

from tests.features.steps.cli_testing import cli_projects
from tests.features.steps.cli_testing import cli_datasets
from tests.features.steps.cli_testing import cli_others

from tests.features.steps.checkout_testing import test_checkout

from tests.features.steps.packages_repo import packages_generate
from tests.features.steps.packages_repo import packages_push
from tests.features.steps.packages_repo import packages_get
from tests.features.steps.packages_repo import packages_list
from tests.features.steps.packages_flow import packages_flow

from tests.features.steps.triggers_repo import test_triggers_create
from tests.features.steps.triggers_repo import test_triggers_get
from tests.features.steps.triggers_repo import test_triggers_list
from tests.features.steps.triggers_repo import test_triggers_update
from tests.features.steps.triggers_repo import test_triggers_delete

from tests.features.steps.services_repo import test_services_deploy
from tests.features.steps.services_repo import test_services_create
from tests.features.steps.services_repo import test_services_get
from tests.features.steps.services_repo import test_services_delete
from tests.features.steps.services_repo import test_services_list
from tests.features.steps.services_repo import test_services_update

from tests.features.steps.filters_entity import test_filters

from tests.features.steps.executions_repo import test_executions_get
from tests.features.steps.executions_repo import test_executions_create
from tests.features.steps.executions_repo import test_executions_list
from tests.features.steps.executions_repo import test_executions_multiple
from tests.features.steps.execution_monitoring import test_execution_monitoring

from tests.features.steps.bots_repo import test_bots_create
from tests.features.steps.bots_repo import test_bots_list
from tests.features.steps.bots_repo import test_bots_get
from tests.features.steps.bots_repo import test_bots_delete

from tests.features.steps.artifacts_repo import test_artifacts_upload
from tests.features.steps.artifacts_repo import test_artifacts_get
from tests.features.steps.artifacts_repo import test_artifacts_list
from tests.features.steps.artifacts_repo import test_artifacts_download
from tests.features.steps.artifacts_repo import test_artifacts_delete

from tests.features.steps.tasks_repo import test_tasks_create
from tests.features.steps.tasks_repo import test_tasks_get
from tests.features.steps.tasks_repo import test_tasks_list
from tests.features.steps.tasks_repo import test_tasks_delete
from tests.features.steps.tasks_repo import test_tasks_qa_task
from tests.features.steps.tasks_repo import test_tasks_add_and_get_items

from tests.features.steps.assignments_repo import test_assignments_create
from tests.features.steps.assignments_repo import test_assignments_get
from tests.features.steps.assignments_repo import test_assignments_list
from tests.features.steps.assignments_repo import test_assignments_delete
from tests.features.steps.assignments_repo import test_assignments_reassign
from tests.features.steps.assignments_repo import test_assignments_redistribute
from tests.features.steps.assignments_repo import test_assignments_items_operations

from tests.features.steps.converter import converter
