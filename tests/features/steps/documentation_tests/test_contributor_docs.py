import behave
import os
import dtlpy as dl


@behave.when(u'List Members')
def step_impl(context):
    context.members_list = context.project.list_members(role=dl.MemberRole.OWNER)  # View all annotators in a project


@behave.given(u'Add Members "{member_email}" as "{member_role}"')
@behave.when(u'Add Members "{member_email}" as "{member_role}"')
@behave.then(u'Add Members "{member_email}" as "{member_role}"')
def step_impl(context, member_email, member_role):
    if member_email == "user":
        member_email = os.environ["TEST_USERNAME"]
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


@behave.when(u'I add "{user_email}" as "{role}" to organization')
def step_impl(context, user_email, role):
    # role = owner / admin / member / worker
    if user_email == "user":
        user_email = os.environ["TEST_USERNAME"]
    if user_email not in [member.email for member in context.organization.list_members()]:
        context.organization.add_member(email=user_email, role=role)  # role is optional - default is member
        context.org_members = context.org_members + 1


@behave.then(u'I validate "{user_email}" is a "{role}" in organization')
def step_impl(context, user_email, role):
    context.organization = context.dl.organizations.get(organization_id=context.organization.id)
    # role = owner / admin / member / worker
    if user_email == "user":
        user_email = os.environ["TEST_USERNAME"]
    for user in context.organization.list_members():
        if user_email == user.email:
            if role == user.role:
                if context.org_members == len(context.organization.list_members()):
                    break
                else:
                    raise Exception(f"expected {context.org_members} members, got {len(context.organization.list_members())}")
            else:
                raise Exception(f"expected {context.org_members} role, got {len(context.organization.list_members())}")
    else:
        raise Exception(f"expected {user_email} to be a member of the organization")


@behave.when(u'I remove "{user_email}" from organization')
def step_impl(context, user_email):
    if user_email == "user":
        user_email = os.environ["TEST_USERNAME"]
    if user_email in [member.email for member in context.organization.list_members()]:
        context.organization.delete_member(user_id=user_email, sure=True, really=True)
        context.org_members = context.org_members - 1
    else:
        raise Exception(f"{user_email} is not a member of the organization")


@behave.when(u'I get organization')
def step_impl(context):
    context.organization = context.dl.organizations.get(organization_id=context.project.org["id"])
    context.org_members = len(context.organization.list_members())
