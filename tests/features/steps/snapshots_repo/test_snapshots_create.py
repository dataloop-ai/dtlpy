import behave
import random
import string
import os


@behave.when(u'I create a snapshot with a random name')
@behave.given(u'I create a snapshot with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    snapshot_name = 'random_snapshot_{}'.format(rand_str)
    # create dataset
    try:
        context.dataset = context.project.datasets.get('snapshot_dataset')
    except context.dl.exceptions.NotFound:
        context.dataset = context.project.datasets.create('snapshot_dataset')
    # create snapshot
    context.snapshot = context.model.snapshots.create(snapshot_name=snapshot_name,
                                                      dataset_id=context.dataset.id,
                                                      ontology_id=context.dataset.ontology_ids[0])
    if not hasattr(context, 'snapshot_count'):
        context.snapshot_count = 0
    context.snapshot_count += 1


@behave.then(u'Snapshot object with the same name should be exist')
def step_impl(context):
    assert isinstance(context.snapshot, context.dl.entities.Snapshot)


@behave.then(u'Snapshot object with the same name should be exist in host')
def step_impl(context):
    snapshot_get = context.model.snapshots.get(snapshot_name=context.snapshot.name)
    assert snapshot_get.to_json() == context.snapshot.to_json()


@behave.when(u'I create a snapshot with the same name')
def step_impl(context):
    try:
        context.model.snapshots.create(snapshot_name=context.snapshot.name,
                                       dataset_id=context.dataset.id,
                                       ontology_id=context.dataset.ontology_ids[0])
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No snapshot was created')
def step_impl(context):
    assert len(context.model.snapshots.list()) == context.snapshot_count


@behave.when(u'I push bucket from "{bucket_path}"')
def step_impl(context, bucket_path):
    try:
        codebase_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], bucket_path)
        bucket = context.snapshot.buckets.create()
        bucket.upload(codebase_path)
        context.snapshot.bucket = bucket
        context.snapshot.update()
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Snapshot object has ItemBucket')
def step_impl(context):
    snapshot = context.dl.snapshots.get(snapshot_id=context.snapshot.id)
    assert isinstance(snapshot.bucket, context.dl.ItemBucket)
