import behave
import dtlpy as dl


@behave.when(u'List Members')
def step_impl(context):
    context.members_list = context.project.list_members(role=dl.MemberRole.OWNER)  # View all annotators in a project


@behave.then(u'Add Members "{member_email}" as "{member_role}"')
def step_impl(context, member_email, member_role):
    context.project.add_member(email=member_email, role=member_role)  # role is optional - default is developer


@behave.then(u'Update Members "{member_email}" to "{member_role}"')
def step_impl(context, member_email, member_role):
    context.project.update_member(email=member_email, role=member_role)  # Update user to annotation manager


@behave.then(u'Remove Members "{annotator_email}"')
def step_impl(context, annotator_email):
    context.project.remove_member(email=annotator_email)  # Remove contributor from project
