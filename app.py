from abc import ABC, abstractmethod


import gradio as gr


MAX_INPUTS = 10
MAX_TASKS = 50


class Component(ABC):
    def __init__(self, visible: bool = False):
        self.component = None
        self.visible = visible

    @abstractmethod
    def render(self) -> gr.Box:
        ...


class Input(Component):
    def render(self) -> None:
        with gr.Box(visible=self.visible) as component:
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
        self.component = component


class AITask(Component):
    def render(self) -> None:
        with gr.Box(visible=self.visible) as component:
            gr.Markdown(f"AI task")
            with gr.Row():
                with gr.Column():
                    self.prompt = gr.Textbox(
                        label="Instructions",
                        lines=15,
                        interactive=True,
                        placeholder="What is the AI assistant meant to do?",
                    )
                with gr.Column():
                    with gr.Box():
                        self.output_name = gr.Textbox(
                            label="Output name", interactive=True, placeholder="var"
                        )
                        self.output = gr.Textbox(
                            label="",
                            lines=10,
                            interactive=False,
                        )
            self.component = component


all_inputs = [Input() for _ in range(MAX_INPUTS)]
all_tasks = [AITask() for _ in range(MAX_TASKS)]

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


with gr.Blocks() as demo:
    # Layout
    for i in all_inputs:
        i.render()
    with gr.Row():
        add_input_btn = gr.Button("Add input variable")
        remove_input_btn = gr.Button("Remove input variable")
    execute_btn = gr.Button("Execute")
    for t in all_tasks:
        t.render()
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")

    # Event handling
    add_input_btn.click(
        add_input,
        inputs=[],
        outputs=[i.component for i in all_inputs],
    )
    remove_input_btn.click(
        remove_input,
        inputs=[],
        outputs=[i.component for i in all_inputs],
    )
    add_task_btn.click(
        add_task,
        inputs=[],
        outputs=[t.component for t in all_tasks],
    )
    remove_task_btn.click(
        remove_task,
        inputs=[],
        outputs=[t.component for t in all_tasks],
    )

demo.launch()
