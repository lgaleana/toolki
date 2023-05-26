import re
from typing import Dict, Optional, Union

import gradio as gr

import ai


MAX_INPUTS = 10
MAX_TASKS = 10


class Input:
    vname = "v"

    def render(self, id_: int, visible: bool) -> gr.Textbox:
        self.output = gr.Textbox(
            label=f"Input: {{{self.vname}{id_}}}",
            interactive=True,
            placeholder="Variable value",
            visible=visible,
        )
        return self.output

    def execute(self) -> None:
        pass


class AITask:
    vname = "t"

    def render(self, id_: int, visible: bool) -> gr.Box:
        with gr.Box(visible=visible) as gr_component:
            gr.Markdown(f"AI task")
            with gr.Row():
                self.prompt = gr.Textbox(
                    label="Instructions",
                    lines=10,
                    interactive=True,
                    placeholder="What is the AI assistant meant to do?",
                )
                self.output = gr.Textbox(
                    label=f"Output: {{{self.vname}{id_}}}",
                    lines=10,
                    interactive=False,
                )
            return gr_component

    def execute(self, prompt: str, prompt_vars: Dict[str, str]) -> Optional[str]:
        if prompt:
            formatted_prompt = prompt.format(**prompt_vars)
            return ai.llm.next([{"role": "user", "content": formatted_prompt}])


class Component:
    def __init__(self, id_: int, internal: Union[Input, AITask], visible: bool = False):
        # Internal state
        self._id = id_
        self.internal = internal
        self._source = self.internal.__class__.__name__
        self._initial_visibility = visible

        # Gradio state
        self.component_id: gr.Number
        self.visible: gr.Number
        self.gr_component = gr.Box
        self.output: gr.Textbox

    def render(self) -> None:
        self.component_id = gr.Number(value=self._id, visible=False)
        self.visible = gr.Number(int(self._initial_visibility), visible=False)
        self.gr_component = self.internal.render(self._id, self._initial_visibility)
        self.output = self.internal.output

    def execute(self, *args):
        print(f"Executing component :: {self._source}.{self._id}")
        return self.internal.execute(*args)


all_inputs = {i: Component(i, Input()) for i in range(MAX_INPUTS)}
all_tasks = {i: Component(i, AITask()) for i in range(MAX_TASKS)}

all_inputs[0]._initial_visibility = True
all_tasks[0]._initial_visibility = True


def _get_all_vars_up_to(to: int):
    return [in_.output for in_ in all_inputs.values()] + [
        t.output for i, t in all_tasks.items() if i < to
    ]


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


with gr.Blocks() as demo:
    # Initial layout
    gr.Markdown(
        """
    # Toolkit
    Define input variables to be used in your tasks.
    <br>Task outputs can be used in subsequent tasks.
    <br>
    <br>AI tasks call into ChatGPT to perform actions.
    <br>Chain inputs and tasks to build an E2E application.
    <br>
    <br>Example prompt: "Translate the following text into spanish and add {v0} more sentences: {t0}".
    """
    )
    for i in all_inputs.values():
        i.render()
    with gr.Row():
        add_input_btn = gr.Button("Add input variable")
        remove_input_btn = gr.Button("Remove input variable")
    for t in all_tasks.values():
        t.render()
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")
    error_message = gr.HighlightedText(value=None, visible=False)
    execute_btn = gr.Button("Execute")

    # Edit layout
    add_input_btn.click(
        add_input,
        inputs=[i.visible for i in all_inputs.values()],
        outputs=[i.gr_component for i in all_inputs.values()]  # type: ignore
        + [i.visible for i in all_inputs.values()],
    )
    remove_input_btn.click(
        remove_input,
        inputs=[i.visible for i in all_inputs.values()],
        outputs=[i.gr_component for i in all_inputs.values()]  # type: ignore
        + [i.visible for i in all_inputs.values()],
    )
    add_task_btn.click(
        add_task,
        inputs=[i.visible for i in all_tasks.values()],
        outputs=[i.gr_component for i in all_tasks.values()]  # type: ignore
        + [i.visible for i in all_tasks.values()],
    )
    remove_task_btn.click(
        remove_task,
        inputs=[i.visible for i in all_tasks.values()],
        outputs=[i.gr_component for i in all_tasks.values()]  # type: ignore
        + [i.visible for i in all_tasks.values()],
    )

    # Sequential execution
    execution_event = execute_btn.click(
        _clear_error, inputs=[], outputs=[error_message]
    )
    for i, task in all_tasks.items():
        execution_event = execution_event.then(
            execute_task,
            inputs=[task.component_id, task.internal.prompt, error_message] + _get_all_vars_up_to(i),  # type: ignore
            outputs=[task.output, error_message],
        )

demo.launch()
