import behave
import threading
import dtlpy as dl
from operator import attrgetter


@behave.when('I Exporting the dataset')
def step_impl(context):
    def export_with_thread():
        try:
            context.dataset.export(local_path=context.folder_path)
        except Exception as e:
            context.export_error = e

    context.buffer = threading.Thread(target=export_with_thread)
    context.buffer.start()


@behave.when('I send "{type}" request with "{path}" and params')
def step_impl(context, type, path):
    context.data = {row[0]: row[1] for row in context.table}
    if "projects" in context.data:
        context.data["projects"] = [attrgetter(context.data["projects"])(context)]
    if "datasetId" in context.data:
        context.data["datasetId"] = attrgetter(context.data["datasetId"])(context)

    success, context.response = dl.client_api.gen_request(
        req_type=type,
        path=path,
        json_req=context.data
    )
    assert success


@behave.then('I expect status will be "{status}"')
def step_impl(context, status):
    response = context.response
    response_dict = response.json()
    records = response_dict.get("records", [])
    if not records:
        raise AssertionError(f"Test Failed: No records found in response: {response_dict}")
    response_status = records[0].get("status", "UNKNOWN")
    assert status == response_status, f"Test Failed, Expected {status} but got {response_status}"
    if getattr(context, "buffer", None) and context.buffer.is_alive():
        context.buffer.join()
