import behave
import dictdiffer


@behave.when(u'I reassign assignment to "{new_assignee}"')
def step_impl(context, new_assignee):
    context.reassigned = context.assignment.reassign(assignee_id=new_assignee)


@behave.then(u'Assignments was reassigned to "{new_assignee}"')
def step_impl(context, new_assignee):
    assignment_json = context.reassigned.to_json()
    org_assignment_json = context.assignment.to_json()
    assignment_json.pop('annotator')
    org_assignment_json.pop('annotator')
    assignment_json.pop('url')
    org_assignment_json.pop('url')
    assignment_json.pop('id')
    org_assignment_json.pop('id')
    assignment_json.pop('name')
    org_assignment_json.pop('name')
    success = assignment_json == org_assignment_json
    if not success:
        diffs = list(dictdiffer.diff(org_assignment_json, assignment_json))
        print(diffs)
    success = success and context.reassigned.annotator == new_assignee
    assert success


