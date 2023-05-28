from abc import ABC, abstractmethod
from typing import List, Union

import gradio as gr
import requests

import ai


class Component(ABC):
    def __init__(self, id_: int, visible: bool = False):
        # Internal state
        self._id = id_
        self._source = self.__class__.__name__
        self.vname: str

        # Gradio state
        self.component_id: gr.Number
        self.gr_component: Union[gr.Box, gr.Textbox]
        self.output: gr.Textbox
        self.visible: gr.Number

    def render(self) -> None:
        self.component_id = gr.Number(value=self._id, visible=False)
        self.visible = gr.Number(0, visible=False)
        self.gr_component = self._render(self._id)

    @abstractmethod
    def _render(self, id_: int) -> Union[gr.Box, gr.Textbox]:
        ...


class Input(Component):
    vname = "v"

    def _render(self, id_: int) -> gr.Textbox:
        self.output = gr.Textbox(
            label=f"Input: {{{self.vname}{id_}}}",
            interactive=True,
            placeholder="Variable value",
            visible=False,
        )
        return self.output


class TaskComponent(ABC):
    vname = "t"

    def __init__(self):
        self.name: str
        self.gr_component: gr.Box
        self.input: gr.Textbox
        self.output: gr.Textbox

    def render(self, id_: int) -> None:
        self.gr_component = self._render(id_)
        self.gr_component.visible = False

    @abstractmethod
    def _render(self, id_) -> gr.Box:
        ...

    @abstractmethod
    def execute(self, input):
        ...


class AITask(TaskComponent):
    name = "AI Task"

    def _render(self, id_: int) -> gr.Box:
        with gr.Box() as gr_component:
            gr.Markdown("Give instructions to ChatGPT to do something.")
            with gr.Row():
                self.input = gr.Textbox(
                    label="Instructions",
                    lines=10,
                    interactive=True,
                    placeholder="Example: summarize this text: {v0}",
                )
                self.output = gr.Textbox(
                    label=f"Output: {{{self.vname}{id_}}}",
                    lines=10,
                    interactive=False,
                )
            return gr_component

    def execute(self, prompt: str) -> str:
        return ai.llm.next([{"role": "user", "content": prompt}])


class VisitURL(TaskComponent):
    name = "Visit URL"

    def _render(self, id_: int) -> gr.Box:
        with gr.Box() as gr_component:
            gr.Markdown("Visit an URL and get its content.")
            with gr.Row():
                self.input = gr.Textbox(
                    interactive=True,
                    placeholder="URL",
                    show_label=False,
                )
                self.output = gr.Textbox(
                    label=f"Output: {{{self.vname}{id_}}}",
                    lines=10,
                    interactive=False,
                )
        return gr_component

    def execute(self, url: str) -> str:
        return requests.get(url).text


class Task(Component):
    available_tasks = [AITask, VisitURL]
    vname = "t"

    def __init__(self, id_: int, visible: bool = False):
        super().__init__(id_, visible)
        self._inner_tasks = [t() for t in self.available_tasks]
        self.gr_component: gr.Box

    def _render(self, id_: int) -> gr.Box:
        with gr.Box(visible=False) as gr_component:
            self.task_picker = gr.Dropdown(
                [AITask.name, VisitURL.name],
                value=AITask.name,
                label="Pick a new Task",
                type="index",
            )
            self.active_index = gr.Number(-1, visible=False)
            for t in self._inner_tasks:
                t.render(id_)

            self.task_picker.select(
                self.pick_task,
                inputs=[self.task_picker],
                outputs=[t.gr_component for t in self._inner_tasks],
            )
        return gr_component

    @staticmethod
    def pick_task(idx):
        update = [gr.Box.update(visible=False)] * len(Task.available_tasks)
        update[idx] = gr.Box.update(visible=True)
        return update

    def inputs(self) -> List[gr.Textbox]:
        return [t.input for t in self._inner_tasks]

    def outputs(self) -> List[gr.Textbox]:
        return [t.output for t in self._inner_tasks]

    def execute(self, active_index, input):
        inner_task = self._inner_tasks[active_index]
        print(f"Executing {inner_task._source}: {inner_task._id}")
        return inner_task.execute(input)


MAX_TASKS = 10

all_tasks = {i: Task(i) for i in range(MAX_TASKS)}


class Tasks:
    @classmethod
    def visibilities(cls) -> List[gr.Number]:
        return [t.visible for t in all_tasks.values()]

    @classmethod
    def active_indexes(cls) -> List[gr.Number]:
        return [t.active_index for t in all_tasks.values()]

    @classmethod
    def gr_components(cls) -> List[gr.Box]:
        return [t.gr_component for t in all_tasks.values()]
