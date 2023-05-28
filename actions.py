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
    # We need to return outputs for all tasks in the row.
    outputs = [""] * n_avail_tasks

    if (
        active_index is None or error_value
    ):  # Active index could be 0 == not active_index
        return outputs + [
            gr.HighlightedText.update(
                value=error_value, visible=error_value is not None
            )
        ]

    task_id = int(task_id)
    active_index = int(active_index)
    inner_n_inputs = all_tasks[task_id].inner_n_inputs

    start_inputs = 0
    end_inputs = 0
    end_all_inputs = sum(inner_n_inputs)
    for i, n in enumerate(inner_n_inputs):
        if i == active_index:
            end_inputs = start_inputs + n
            break
        start_inputs += n
    task_inputs = args[start_inputs:end_inputs]
    prev_active_indexes = args[end_all_inputs : end_all_inputs + task_id]
    prev_task_outputs = args[end_all_inputs + task_id :]
    non_empty_inputs = [i for i in task_inputs if i]

    if len(non_empty_inputs) < len(task_inputs):
        return outputs + [
            gr.HighlightedText.update(
                value=[(f"Missing inputs for Task: {task_id}", "ERROR")],
                visible=True,
            )
        ]

    vars_in_scope = {}
    for i, prev_active_index in enumerate(prev_active_indexes):
        vars_in_scope[f"{Task.vname}{i}"] = prev_task_outputs[
            i * n_avail_tasks + int(prev_active_index)
        ]
    # Get all variables referenced within the task input
    prompt_vars = [v for ti in non_empty_inputs for v in re.findall("{(.*?)}", ti)]

    # If there is an undefined variable referenced, HighlightedText will signal the error.
    undefined_vars = prompt_vars - vars_in_scope.keys()
    if len(undefined_vars) > 0:
        outputs[active_index] = "ERROR"
        return outputs + [
            gr.HighlightedText.update(
                value=[
                    (
                        f"The variables in Task :: {task_id} are being used before being defined :: {undefined_vars}. Please check your tasks.",
                        "ERROR",
                    )
                ],
                visible=True,
            )
        ]

    try:
        # Task logic gets inserted into the right index
        outputs[active_index] = all_tasks[task_id].execute(
            active_index, *non_empty_inputs, vars_in_scope=vars_in_scope
        )
        return outputs + [
            gr.HighlightedText.update(
                value=error_value, visible=error_value is not None
            )
        ]
    except Exception as e:
        import traceback

        print(traceback.format_tb(e.__traceback__))
        outputs[active_index] = "ERROR"
        return outputs + [
            gr.HighlightedText.update(
                value=[(f"Error in Task {task_id} :: {e}", "ERROR")],
                visible=True,
            )
        ]
