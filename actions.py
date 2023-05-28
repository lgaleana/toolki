import re
from typing import List

import gradio as gr

from components import Input, State as s, Task


def _is_task_row_fully_invisible(row: List[int]) -> bool:
    for visible in row:
        if bool(visible):
            return False
    return True


def add_task(index, *visibility):
    visibility = list(visibility)
    n_avail_tasks = len(Task.available_tasks)

    for i in range(s.MAX_TASKS):
        start_row = i * n_avail_tasks
        is_row_invisible = _is_task_row_fully_invisible(
            visibility[start_row : start_row + n_avail_tasks]
        )
        if is_row_invisible:
            unchanged_up_to = start_row + index
            return (
                [gr.Box.update()] * unchanged_up_to
                + [gr.Box.update(visible=True)]
                + [gr.Box.update()] * (len(visibility) - unchanged_up_to - 1)
                + [gr.Number.update()] * unchanged_up_to
                + [1]
                + [gr.Number.update()] * (len(visibility) - unchanged_up_to - 1)
            )
    return [gr.Box.update()] * len(visibility) + [gr.Number.update()] * len(visibility)


def remove_task(*visibility):
    visibility = list(visibility)
    n_avail_tasks = len(Task.available_tasks)

    for i in range(s.MAX_TASKS):
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


def execute_task(id_: int, prev_error_value, n_task_inputs, *vars_in_scope):
    """
    Params:
        - id_: This will tell us which task to execute.
        - prev_error_value: I carry around whether there is an error in the execution, to be displayed at the end.
        - n_task_inputs: How many inputs does this task have?
        - vars_in_scope: All variables in scope. This can be a) input varaibles, b) task inputs or c) previous task outputs.
    """
    n_task_inputs = int(n_task_inputs)
    task_inputs = vars_in_scope[:n_task_inputs]
    task_outputs = vars_in_scope[n_task_inputs:]
    non_empty_task_inputs = [ti for ti in task_inputs if ti]

    # Put all defined variables into a dict, with names (except task inputs)
    vars.update(
        {f"{Task.vname}{i}": task_output for i, task_output in enumerate(task_outputs)}
    )
    # Get all variables referenced within the task inputs
    prompt_vars = {v for ti in non_empty_task_inputs for v in re.findall("{(.*?)}", ti)}

    # If there is an undefined variable referenced, HighlightedText will signal the error.
    undefined_vars = prompt_vars - vars.keys()
    if len(undefined_vars) > 0:
        return None, gr.HighlightedText.update(
            value=[
                (
                    f"The following variables are being used before being defined :: {undefined_vars}. Please check your tasks.",
                    "ERROR",
                )
            ],
            visible=True,
        )
    error_update = gr.HighlightedText.update(
        value=prev_error_value, visible=prev_error_value is not None
    )

    if non_empty_task_inputs:
        # Execute the task logic
        return (
            s.all_tasks[id_].execute(*non_empty_task_inputs, vars),
            error_update,
        )
    else:
        # There is no actionf for this task.
        return None, error_update
