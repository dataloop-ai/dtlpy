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
from tests.features.steps.datasets_repo import test_datasets_readonly
from tests.features.steps.datasets_repo import test_datasets_download_annotations
from tests.features.steps.datasets_repo import test_dataset_upload_annotations
from tests.features.steps.datasets_repo import test_datasets_download
from tests.features.steps.datasets_repo import test_dataset_context
from tests.features.steps.datasets_repo import tets_dataset_upload_labels

from tests.features.steps.dataset_entity import test_dataset_repo_methods
from tests.features.steps.dataset_entity import test_add_labels_methods

from tests.features.steps.annotations_repo import test_annotations_get
from tests.features.steps.annotations_repo import test_annotations_list
from tests.features.steps.annotations_repo import test_annotations_delete
from tests.features.steps.annotations_repo import test_annotations_download
from tests.features.steps.annotations_repo import test_annotations_update
from tests.features.steps.annotations_repo import test_annotations_upload
from tests.features.steps.annotations_repo import test_annotations_show
from tests.features.steps.annotations_repo import test_annotations_draw
from tests.features.steps.annotations_repo import test_annotations_context

from tests.features.steps.annotation_entity import test_annotation_repo_methods
from tests.features.steps.annotation_entity import test_upload_annotations
from tests.features.steps.annotation_entity import test_annotation_json_to_object
from tests.features.steps.annotation_entity import test_segmentation_to_box

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
from tests.features.steps.items_repo import test_download_and_upload_ndarray_item
from tests.features.steps.items_repo import test_items_context

from tests.features.steps.item_entity import test_item_repo_methods
from tests.features.steps.item_entity import test_item_move
from tests.features.steps.item_entity import test_item_update_status
from tests.features.steps.item_entity import test_item_description

from tests.features.steps.ontologies_repo import test_ontologies_create
from tests.features.steps.ontologies_repo import test_ontologies_get
from tests.features.steps.ontologies_repo import test_ontologies_delete
from tests.features.steps.ontologies_repo import test_ontologies_update

from tests.features.steps.ontology_entity import test_ontology_repo_methods
from tests.features.steps.ontology_entity import test_ontology_attributes
from tests.features.steps.ontology_entity import test_ontology_bamba_icon

from tests.features.steps.recipes_repo import test_recipes_create
from tests.features.steps.recipes_repo import test_recipes_update
from tests.features.steps.recipes_repo import test_recipes_delete
from tests.features.steps.recipes_repo import test_recipes_clone

from tests.features.steps.codebases_repo import test_codebases_pack
from tests.features.steps.codebases_repo import test_codebases_init
from tests.features.steps.codebases_repo import test_codebases_unpack
from tests.features.steps.codebases_repo import test_codebases_get
from tests.features.steps.codebases_repo import test_codebases_list_versions
from tests.features.steps.codebases_repo import test_codebases_list

from tests.features.steps.codebase_entity import test_codebase_repo_methods

from tests.features.steps.command_entity import test_command

from tests.features.steps.utilities import platform_interface_steps

from tests.features.steps.cli_testing import cli_projects
from tests.features.steps.cli_testing import cli_datasets
from tests.features.steps.cli_testing import cli_others

from tests.features.steps.checkout_testing import test_checkout

from tests.features.steps.packages_repo import packages_generate
from tests.features.steps.packages_repo import packages_push
from tests.features.steps.packages_repo import packages_get
from tests.features.steps.packages_repo import packages_list
from tests.features.steps.packages_repo import test_packages_context
from tests.features.steps.packages_repo import packages_name_validation
from tests.features.steps.packages_flow import packages_flow
from tests.features.steps.packages_repo import package_slot
from tests.features.steps.packages_repo import packages_delete

from tests.features.steps.triggers_repo import test_triggers_create
from tests.features.steps.triggers_repo import test_triggers_get
from tests.features.steps.triggers_repo import test_triggers_list
from tests.features.steps.triggers_repo import test_triggers_update
from tests.features.steps.triggers_repo import test_triggers_delete
from tests.features.steps.triggers_repo import test_triggers_context
from tests.features.steps.triggers_repo import test_triggers_item_update
from tests.features.steps.triggers_repo import test_triggers_annotation_update

from tests.features.steps.services_repo import test_services_deploy
from tests.features.steps.services_repo import test_services_create
from tests.features.steps.services_repo import test_services_get
from tests.features.steps.services_repo import test_services_delete
from tests.features.steps.services_repo import test_services_list
from tests.features.steps.services_repo import test_services_update
from tests.features.steps.services_repo import test_services_context

from tests.features.steps.filters_entity import test_filters

from tests.features.steps.executions_repo import test_executions_get
from tests.features.steps.executions_repo import test_executions_create
from tests.features.steps.executions_repo import test_executions_list
from tests.features.steps.executions_repo import test_executions_multiple
from tests.features.steps.executions_repo import test_executions_context
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
from tests.features.steps.tasks_repo import test_task_context
from tests.features.steps.tasks_repo import test_task_priority

from tests.features.steps.assignments_repo import test_assignments_create
from tests.features.steps.assignments_repo import test_assignments_get
from tests.features.steps.assignments_repo import test_assignments_list
from tests.features.steps.assignments_repo import test_assignments_reassign
from tests.features.steps.assignments_repo import test_assignments_redistribute
from tests.features.steps.assignments_repo import test_assignments_items_operations
from tests.features.steps.assignments_repo import test_assignments_context

from tests.features.steps.converter import converter

from tests.features.steps.models_repo import test_models_create
from tests.features.steps.models_repo import test_models_list
from tests.features.steps.models_repo import test_models_delete

from tests.features.steps.model_entity import test_model_name

from tests.features.steps.pipeline_entity import pipeline_get, pipeline_delete, pipeline_update, pipeline_flow
from tests.features.steps.pipeline_entity import pipeline_output_list
from tests.features.steps.features_vectors import test_features_create, test_features_delete
from tests.features.steps.pipeline_entity import test_pipeline_pulling_task

from tests.features.steps.documentation_tests import test_projects_docs
from tests.features.steps.documentation_tests import test_contributor_docs
from tests.features.steps.documentation_tests import test_recipe_docs
from tests.features.steps.documentation_tests import test_dataset_docs

from tests.features.steps.test_cache import test_cache
from tests.features.steps.settings_context import test_settings_context

from tests.features.steps.pipeline_entity import pipeline_reset

from tests.features.steps.items_repo import test_upload_and_download_images

from tests.features.steps.annotations_repo import test_rotated_box_points
from tests.features.steps.app_entity import test_app_install, test_app_uninstall
from tests.features.steps.dpk_tests import dpk_json_to_object, test_dpk_publish, test_dpk_list,\
    test_dpk_pull, test_dpk_get

from tests.features.steps.webm_converter import test_failed_video_message

from tests.features.steps.platform_urls import test_platform_urls

from tests.features.steps.annotation_entity import test_annotation_description

from tests.features.steps.utilities import image_annotations_interface
from tests.features.steps.utilities import video_annotations_interface
from tests.features.steps.utilities import audio_annotations_interface
from tests.features.steps.utilities import text_annotations_interface

from tests.features.steps.utilities import items_interface
from tests.features.steps.utilities import annotations_interface
from tests.features.steps.utilities import projects_interface
from tests.features.steps.utilities import datasets_interface

from tests.features.steps.utilities import conveters_interface