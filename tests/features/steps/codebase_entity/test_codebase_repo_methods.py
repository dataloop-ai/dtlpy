import behave
import os


@behave.given(u'I pack from project.codebases directory by name "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase = context.project.codebases.pack(
        directory=context.codebase_local_dir,
        name=codebase_name,
        description="some description"
    )


@behave.when(u'I unpack a code base entity by the name of "{codebase_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, codebase_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.codebase.unpack(local_path=unpack_path)
    context.unpack_path = unpack_path


@behave.when(u'I list versions of code base entity "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase_version_list = context.codebase.list_versions()
