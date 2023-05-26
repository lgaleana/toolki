from typing import Dict, List, Optional, NamedTuple, Type, Union


import gradio as gr


MAX_INPUTS = 10
MAX_TASKS = 50


class Input:
    def render(self, visible: bool) -> gr.Row:
        with gr.Row(visible=visible) as gr_component:
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
    @property
    def vars(self):
        return [self.prompt]

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
        # Internal state
        self._id = id_
        self.internal = internal
        self.visible = visible

        # Gradio state
        self.component_id: gr.Textbox
        self.source: gr.Textbox
        self.gr_component = gr.Box
        self.output_name: gr.Textbox
        self.output: gr.Textbox

    def render(self) -> None:
        self.component_id = gr.Textbox(value=str(self._id), visible=False)
        self.source = gr.Textbox(value=self.internal.__class__.__name__, visible=False)
        self.gr_component = self.internal.render(bool(self.visible))
        self.output_name = self.internal.output_name
        self.output = self.internal.output


class Variable(NamedTuple):
    source: Type[Union[Input, AITask]]
    id_: int
    name: str
    value: str


all_inputs = {i: Component(i, Input()) for i in range(MAX_INPUTS)}
all_tasks = {i: Component(i, AITask()) for i in range(MAX_TASKS)}

all_inputs[0].visible = True
all_tasks[0].visible = True


def add_input() -> Optional[List[Dict]]:
    for i, input_ in all_inputs.items():
        if not input_.visible:
            input_.visible = True
            return [gr.Row.update(visible=True)] * (i + 1) + [
                gr.Row.update(visible=False)
            ] * (MAX_INPUTS - i)


def remove_input() -> Optional[List[Dict]]:
    for i, input_ in reversed(all_inputs.items()):
        if input_.visible:
            input_.visible = False
            return [gr.Row.update(visible=True)] * i + [
                gr.Row.update(visible=False)
            ] * (MAX_INPUTS - i + 1)


def add_task() -> Optional[List[Dict]]:
    for i, task in all_tasks.items():
        if not task.visible:
            task.visible = True
            return [gr.Box.update(visible=True)] * (i + 1) + [
                gr.Box.update(visible=False)
            ] * (MAX_TASKS - i)


def remove_task() -> Optional[List[Dict]]:
    for i, task in reversed(all_tasks.items()):
        if task.visible:
            task.visible = False
            return [gr.Box.update(visible=True)] * i + [
                gr.Box.update(visible=False)
            ] * (MAX_TASKS - i + 1)


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

    # Layout editing
    add_input_btn.click(
        add_input,
        inputs=[],
        outputs=[i.gr_component for i in all_inputs.values()],
    )
    remove_input_btn.click(
        remove_input,
        inputs=[],
        outputs=[i.gr_component for i in all_inputs.values()],
    )
    add_task_btn.click(
        add_task,
        inputs=[],
        outputs=[t.gr_component for t in all_tasks.values()],
    )
    remove_task_btn.click(
        remove_task,
        inputs=[],
        outputs=[t.gr_component for t in all_tasks.values()],
    )

demo.launch()
