import behave


@behave.when(u'I create Task with priority "{priority}"')
def step_impl(context, priority):
    priorities = {
        "TaskPriority.LOW": context.dl.TaskPriority.LOW,
        "TASK_PRIORITY_LOW": context.dl.TASK_PRIORITY_LOW,
        "TaskPriority.MEDIUM": context.dl.TaskPriority.MEDIUM,
        "TASK_PRIORITY_MEDIUM": context.dl.TASK_PRIORITY_MEDIUM,
        "TaskPriority.HIGH": context.dl.TaskPriority.HIGH,
        "TASK_PRIORITY_HIGH": context.dl.TASK_PRIORITY_HIGH
    }

    context.task = context.dataset.tasks.create(task_name="{}_priority_task".format(priority),
                                                priority=priorities[priority])


@behave.then(u'Task with priority "{priority}" got created')
def step_impl(context, priority):
    priorities = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    assert context.task.priority == priorities[priority]
