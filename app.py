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


def execute_task(id_: int, prompt: str, *vars):
    inputs = vars[:MAX_INPUTS]
    task_outputs = vars[MAX_INPUTS:]

    prompt_vars = {
        f"{Input.vname}{i}": input_ for i, input_ in enumerate(inputs) if input_
    }
    prompt_vars.update(
        {f"{AITask.vname}{i}": task for i, task in enumerate(task_outputs)}
    )

    if prompt:
        return all_tasks[id_].execute(prompt, prompt_vars)


with gr.Blocks() as demo:
    # Initial layout
    for i in all_inputs.values():
        i.render()
    input_error = gr.HighlightedText(
        [("Repeated variable names in inputs. Please pick different names.", "Error")],
        show_label=False,
        visible=False,
    )
    with gr.Row():
        add_input_btn = gr.Button("Add input variable")
        remove_input_btn = gr.Button("Remove input variable")
    execute_btn = gr.Button("Execute")
    for t in all_tasks.values():
        t.render()
    task_error = gr.HighlightedText(
        [("Repeated variable names in tasks. Please pick different names.", "Error")],
        show_label=False,
        visible=False,
    )
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")

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
        execute_task,
        inputs=[all_tasks[0].component_id, all_tasks[0].internal.prompt] + _get_all_vars_up_to(0),  # type: ignore
        outputs=[all_tasks[0].output],
    )
    for i, task in list(all_tasks.items())[1:]:
        execution_event = execution_event.then(
            execute_task,
            inputs=[task.component_id, task.internal.prompt] + _get_all_vars_up_to(i),  # type: ignore
            outputs=[task.output],
        )

demo.launch()
