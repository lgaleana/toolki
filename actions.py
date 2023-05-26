import re

import gradio as gr

from components import all_inputs, all_tasks, Input, MAX_INPUTS, MAX_TASKS, Task


def add_input(*visibility):
    for i, visible in enumerate(visibility, 1):
        if not bool(visible):
            return (
                [gr.Textbox.update(visible=True)] * i
                + [gr.Textbox.update(visible=False, value="")] * (MAX_INPUTS - i)
                + [1] * i
                + [0] * (MAX_INPUTS - i)
            )


def remove_input(*visibility):
    for i, visible in reversed(list(enumerate(visibility, 1))):
        if bool(visible):
            return (
                [gr.Textbox.update(visible=True)] * (i - 1)
                + [gr.Textbox.update(visible=False, value="")] * (MAX_INPUTS - i + 1)
                + [1] * (i - 1)
                + [0] * (MAX_INPUTS - i + 1)
            )


def add_task(*visibility):
    for i, visible in enumerate(visibility, 1):
        if not bool(visible):
            return (
                [gr.Box.update(visible=True)] * i
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i)
                + [1] * i
                + [0] * (MAX_TASKS - i)
            )


def remove_task(*visibility):
    for i, visible in reversed(list(enumerate(visibility, 1))):
        if bool(visible):
            return (
                [gr.Box.update(visible=True)] * (i - 1)
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i + 1)
                + [1] * (i - 1)
                + [0] * (MAX_TASKS - i + 1)
            )


def _get_all_vars_up_to(to: int):
    return [in_.output for in_ in all_inputs.values()] + [
        t.output for i, t in all_tasks.items() if i < to
    ]


def _clear_error():
    return gr.HighlightedText.update(value=None, visible=False)


def execute_task(id_: int, prev_error_value, n_inputs, *vars_in_scope):
    """
    Params:
        - id_: This will tell us which task to execute.
        - prev_error_value: I carry around whether there is an error in the execution, to be displayed at the end.
        - n_inputs: How many inputs does this task have?
        - vars: All variables in scope. This can be a) task inputs, input varaibles or previous task outputs.
    """
    n_inputs = int(n_inputs)
    task_inputs = vars_in_scope[:n_inputs]
    input_vars = vars_in_scope[n_inputs:MAX_INPUTS]
    task_outputs = vars_in_scope[MAX_INPUTS:]
    non_empty_task_inputs = [ti for ti in task_inputs if ti]

    # Put all defined variables into a dict, with names (except task inputs)
    vars = {
        f"{Input.vname}{i}": input_ for i, input_ in enumerate(input_vars) if input_
    }
    vars.update(
        {f"{Task.vname}{i}": task for i, task in enumerate(task_outputs)}
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
            all_tasks[id_].execute(*non_empty_task_inputs, vars),
            error_update,
        )
    else:
        # There is no actionf or this task.
        return None, error_update
