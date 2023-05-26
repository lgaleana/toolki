from typing import NamedTuple, Type, Union


import gradio as gr


MAX_INPUTS = 10
MAX_TASKS = 50


class Input:
    def render(self, visible: bool) -> gr.Box:
        with gr.Box(visible=visible) as gr_component:  # TODO: Remove this
            with gr.Row():
                self.output_name = gr.Textbox(
                    label="Input name (can be referenced with {})",
                    interactive=True,
                    placeholder="Variable name",
                )
                self.output = gr.Textbox(
                    label="Input value",
                    interactive=True,
                    placeholder="Variable value",
                )
        return gr_component


class AITask:
    def render(self, visible: bool) -> gr.Box:
        with gr.Box(visible=visible) as gr_component:
            gr.Markdown(f"AI task")
            with gr.Row():
                with gr.Column():
                    self.prompt = gr.Textbox(
                        label="Instructions",
                        lines=13,
                        interactive=True,
                        placeholder="What is the AI assistant meant to do?",
                    )
                with gr.Column():
                    self.output_name = gr.Textbox(
                        label="Output name (can be referenced with {})",
                        interactive=True,
                        placeholder="Variable name",
                    )
                    self.output = gr.Textbox(
                        show_label=False,
                        lines=10,
                        interactive=False,
                    )
            return gr_component


class Component:
    def __init__(self, id_: int, internal: Union[Input, AITask], visible: bool = False):
        self._id = id_
        self.component_id: gr.Textbox
        self._internal = internal
        self.gr_component = gr.Box
        self.visible = visible
        self.output_name: gr.Textbox
        self.output: gr.Textbox
        self.source: gr.Textbox

    def render(self) -> None:
        self.component_id = gr.Textbox(value=str(self._id), visible=False)
        self.source = gr.Textbox(value=self._internal.__class__.__name__, visible=False)
        self.gr_component = self._internal.render(self.visible)
        self.output_name = self._internal.output_name
        self.output = self._internal.output


class Variable(NamedTuple):
    source: Type[Union[Input, AITask]]
    id_: int
    name: str
    value: str


all_inputs = [Component(i, Input()) for i in range(MAX_INPUTS)]
all_tasks = [Component(i, AITask()) for i in range(MAX_TASKS)]
all_components = all_inputs + all_tasks
all_variables = {}  # Will be updated once rendered

all_inputs[0].visible = True
all_tasks[0].visible = True
next_input = 1
next_task = 1


def _update_components(i: int, max: int):
    return [gr.Box.update(visible=True)] * i + [gr.Box.update(visible=False)] * (
        max - i
    )


def add_input():
    global next_input
    if next_input < MAX_INPUTS:
        next_input += 1
    return _update_components(next_input, MAX_INPUTS)


def remove_input():
    global next_input
    if next_input > 0:
        next_input -= 1
    return _update_components(next_input, MAX_INPUTS)


def add_task():
    global next_task
    if next_task < MAX_TASKS:
        next_task += 1
    return _update_components(next_task, MAX_TASKS)


def remove_task():
    global next_task
    if next_task > 0:
        next_task -= 1
    return _update_components(next_task, MAX_TASKS)


def execute(output_names, outputs):
    for output_name in output_names:
        print(output_name)


def update_scope_variables(component_id, source, output_name, output):
    all_variables[f"{source}.{component_id}"] = Variable(
        component_id, source, output_name, output
    )
    print(all_variables)


with gr.Blocks() as demo:
    # Initial layout
    for i in all_inputs:
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
    for t in all_tasks:
        t.render()
    task_error = gr.HighlightedText(
        [("Repeated variable names in tasks. Please pick different names.", "Error")],
        show_label=False,
        visible=False,
    )
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")

    # Layout editing
    add_input_btn.click(
        add_input,
        inputs=[],
        outputs=[i.gr_component for i in all_inputs],
    )
    remove_input_btn.click(
        remove_input,
        inputs=[],
        outputs=[i.gr_component for i in all_inputs],
    )
    add_task_btn.click(
        add_task,
        inputs=[],
        outputs=[t.gr_component for t in all_tasks],
    )
    remove_task_btn.click(
        remove_task,
        inputs=[],
        outputs=[t.gr_component for t in all_tasks],
    )

    # Execution
    for c in all_components:
        c.output_name.change(
            update_scope_variables,
            inputs=[c.component_id, c.source, c.output_name, c.output],
            outputs=[],
        )

demo.launch()
