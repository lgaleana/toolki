import re
from typing import List

import gradio as gr

from components import MAX_TASKS, all_tasks, Task


def _is_task_row_fully_invisible(row: List[int]) -> bool:
    for visible in row:
        if bool(visible):
            return False
    return True


def add_task(index, *visibility):
    visibility = list(visibility)
    n_avail_tasks = len(Task.available_tasks)

    for i in range(MAX_TASKS):
        start_row = i * n_avail_tasks
        is_row_invisible = _is_task_row_fully_invisible(
            visibility[start_row : start_row + n_avail_tasks]
        )
        if is_row_invisible:
            unchanged_up_to = start_row + index
            return (
                [gr.Number.update()] * i
                + [index]
                + [gr.Number.update()] * (MAX_TASKS - i - 1)
                + [gr.Box.update()] * unchanged_up_to
                + [gr.Box.update(visible=True)]
                + [gr.Box.update()] * (len(visibility) - unchanged_up_to - 1)
                + [gr.Number.update()] * unchanged_up_to
                + [1]
                + [gr.Number.update()] * (len(visibility) - unchanged_up_to - 1)
            )
    return (
        [gr.Number.update()] * MAX_TASKS
        + [gr.Box.update()] * len(visibility)
        + [gr.Number.update()] * len(visibility)
    )


def remove_task(*visibility):
    visibility = list(visibility)
    n_avail_tasks = len(Task.available_tasks)

    for i in range(MAX_TASKS):
        start_row = i * n_avail_tasks
        is_row_invisible = _is_task_row_fully_invisible(
            visibility[start_row : start_row + n_avail_tasks]
        )
        if is_row_invisible:
            unchanged_up_to = start_row - n_avail_tasks
            return (
                [gr.Box.update()] * unchanged_up_to
                + [gr.Box.update(visible=False)] * (len(visibility) - unchanged_up_to)
                + [gr.Number.update()] * unchanged_up_to
                + [0] * (len(visibility) - unchanged_up_to)
            )
    return (
        [gr.Box.update()] * (len(visibility) - n_avail_tasks)
        + [gr.Box.update(visible=False)] * n_avail_tasks
        + [gr.Number.update()] * (len(visibility) - n_avail_tasks)
        + [0] * (len(visibility) - n_avail_tasks)
    )


def execute_task(task_id: int, active_index: int, error_value, *args):
    """
    Params:
        - task_id: This will tell us which task to execute.
        - active_index: The index of the actual task that is visible.
        - prev_error_value: I carry around whether there is an error in the execution, to be displayed at the end.
        - args: Other variables that will be decomposed.
    """
    task_id = int(task_id)
    active_index = int(active_index)
    n_avail_tasks = len(Task.available_tasks)

    task_input = args[:n_avail_tasks][active_index]
    prev_active_indexes = args[n_avail_tasks : n_avail_tasks + task_id]
    prev_task_outputs = args[n_avail_tasks + task_id :]

    error_update = gr.HighlightedText.update(
        value=error_value, visible=error_value is not None
    )
    # We need to return outputs for all tasks in the row.
    outputs = [""] * n_avail_tasks

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
