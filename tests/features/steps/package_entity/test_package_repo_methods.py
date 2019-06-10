import behave
import os


@behave.given(u'I pack from project.packages directory by name "{package_name}"')
def step_impl(context, package_name):
    context.package = context.project.packages.pack(
        directory=context.package_local_dir,
        name=package_name,
        description="some description"
    )


@behave.when(u'I unpack a package entity by the name of "{package_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, package_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.package.unpack(local_path=unpack_path)
    context.unpack_path = unpack_path + "/package"


@behave.when(u'I list versions of package entity "{package_name}"')
def step_impl(context, package_name):
    context.package_version_list = context.package.list_versions()
