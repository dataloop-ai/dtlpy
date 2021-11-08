import behave
import dtlpy as dl


@behave.when(u'List Members')
def step_impl(context):
    context.members_list = context.project.list_members(role=dl.MemberRole.OWNER)  # View all annotators in a project
    # Options:
    dl.MEMBER_ROLE_OWNER
    dl.MEMBER_ROLE_DEVELOPER
    dl.MEMBER_ROLE_ANNOTATOR
    dl.MEMBER_ROLE_ANNOTATION_MANAGER


@behave.then(u'Add Members "{annotator_email}"')
def step_impl(context,annotator_email):
    context.project.add_member(email=annotator_email, role='engineer')  # role is optional - default is developer
    # Options:
    dl.MEMBER_ROLE_OWNER
    dl.MEMBER_ROLE_DEVELOPER
    dl.MEMBER_ROLE_ANNOTATOR
    dl.MEMBER_ROLE_ANNOTATION_MANAGER


@behave.then(u'Update Members "{annotator_email}"')
def step_impl(context,annotator_email):
    context.project.update_member(email=annotator_email, role=dl.MemberRole.ANNOTATION_MANAGER)  # Update user to annotation manager
    # Options:
    dl.MEMBER_ROLE_OWNER
    dl.MEMBER_ROLE_DEVELOPER
    dl.MEMBER_ROLE_ANNOTATOR
    dl.MEMBER_ROLE_ANNOTATION_MANAGER

@behave.then(u'Remove Members "{annotator_email}"')
def step_impl(context,annotator_email):
    context.project.remove_member(email=annotator_email)  # Remove contributor from project
    # Options:
    dl.MEMBER_ROLE_OWNER
    dl.MEMBER_ROLE_DEVELOPER
    dl.MEMBER_ROLE_ANNOTATOR
    dl.MEMBER_ROLE_ANNOTATION_MANAGER