import behave
import dtlpy as dl


@behave.when(u'List Members')
def step_impl(context):
    context.members_list = context.project.list_members(role=dl.MemberRole.OWNER)  # View all annotators in a project


@behave.when(u'Add Members "{member_email}" as "{member_role}"')
@behave.then(u'Add Members "{member_email}" as "{member_role}"')
def step_impl(context, member_email, member_role):
    if member_email not in [member.email for member in context.project.list_members()]:
        context.project.add_member(email=member_email, role=member_role)  # role is optional - default is developer


@behave.when(u'Add Members "{member_email}" as "{member_role}" to project {project_index}')
def step_impl(context, member_email, member_role, project_index):
    if member_email not in [member.email for member in context.projects[int(project_index) - 1].list_members()]:
        context.projects[int(project_index) - 1].add_member(email=member_email, role=member_role)  # role is optional - default is developer


@behave.when(u'Add Members "{member_email}" as "{member_role}" to second_project')
def step_impl(context, member_email, member_role):
    if member_email not in [member.email for member in context.second_project.list_members()]:
        context.second_project.add_member(email=member_email, role=member_role)  # role is optional - default is developer


@behave.then(u'Update Members "{member_email}" to "{member_role}"')
def step_impl(context, member_email, member_role):
    context.project.update_member(email=member_email, role=member_role)  # Update user to annotation manager


@behave.then(u'Remove Members "{annotator_email}"')
def step_impl(context, annotator_email):
    context.project.remove_member(email=annotator_email)  # Remove contributor from project


@behave.When(u'I try to delete a member by email')
def step_impl(context):
    try:
        context.project.remove_member(email=context.bot.email)
        context.error = None
    except Exception as e:
        context.error = e
