import re

import gradio as gr

from components import AITask, all_inputs, all_tasks, Input, MAX_INPUTS, MAX_TASKS


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


def execute_task(id_: int, prompt: str, prev_error_value, *vars):
    inputs = vars[:MAX_INPUTS]
    task_outputs = vars[MAX_INPUTS:]

    prompt_vars = set(re.findall("{(.*?)}", prompt))
    vars_in_scope = {
        f"{Input.vname}{i}": input_ for i, input_ in enumerate(inputs) if input_
    }
    vars_in_scope.update(
        {f"{AITask.vname}{i}": task for i, task in enumerate(task_outputs)}
    )
    undefined_vars = prompt_vars - vars_in_scope.keys()

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

    if prompt:
        return all_tasks[id_].execute(prompt, vars_in_scope), error_update

    return None, error_update
