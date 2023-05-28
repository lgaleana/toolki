import re

import gradio as gr

from components import MAX_TASKS, all_tasks, Task


def add_task(*visibilities):
    for i, visible in enumerate(visibilities, 1):
        if not bool(visible):
            return (
                [gr.Box.update(visible=True)] * i
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i)
                + [1] * i
                + [0] * (MAX_TASKS - i)
            )
    return [gr.Box.update()] * MAX_TASKS + [gr.Number.update()] * MAX_TASKS


def remove_task(*visibilities):
    for i, visible in reversed(list(enumerate(visibilities))):
        if bool(visible):
            return (
                [gr.Box.update(visible=True)] * i
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i)
                + [1] * i
                + [0] * (MAX_TASKS - i)
            )
    return [gr.Box.update()] * MAX_TASKS + [gr.Number.update()] * MAX_TASKS


def execute_task(task_id: int, active_index: int, error_value, *args):
    """
    Params:
        - task_id: This will tell us which task to execute.
        - active_index: The index of the actual task that is visible.
        - prev_error_value: I carry around whether there is an error in the execution, to be displayed at the end.
        - args: Other variables that will be decomposed.
    """
    n_avail_tasks = len(Task.available_tasks)
    error_update = gr.HighlightedText.update(
        value=error_value, visible=error_value is not None
    )
    # We need to return outputs for all tasks in the row.
    outputs = [""] * n_avail_tasks

    if active_index is None:  # Active index could be 0 == not active_index
        return outputs + [error_update]

    task_id = int(task_id)
    active_index = int(active_index)

    task_input = args[:n_avail_tasks][active_index]
    prev_active_indexes = args[n_avail_tasks : n_avail_tasks + task_id]
    prev_task_outputs = args[n_avail_tasks + task_id :]

    if not task_input:
        return outputs + [error_update]

    vars_in_scope = {}
    for i, prev_active_index in enumerate(prev_active_indexes):
        vars_in_scope[f"{Task.vname}{i}"] = prev_task_outputs[
            i * n_avail_tasks + int(prev_active_index)
        ]
    # Get all variables referenced within the task input
    prompt_vars = re.findall("{(.*?)}", task_input)

    # If there is an undefined variable referenced, HighlightedText will signal the error.
    undefined_vars = prompt_vars - vars_in_scope.keys()
    if len(undefined_vars) > 0:
        return outputs + [
            gr.HighlightedText.update(
                value=[
                    (
                        f"The following variables are being used before being defined :: {undefined_vars}. Please check your tasks.",
                        "ERROR",
                    )
                ],
                visible=True,
            )
        ]

    formatted_input = task_input.format(**vars_in_scope)
    # Task logic gets inserted into the right index
    outputs[active_index] = all_tasks[task_id].execute(active_index, formatted_input)
    return outputs + [error_update]
