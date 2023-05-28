from abc import ABC, abstractmethod
from typing import List

import gradio as gr
import requests

import ai


class Component(ABC):
    vname = None

    def __init__(self, id_: int, visible: bool = False):
        # Internal state
        self._id = id_
        self._source = self.__class__.__name__
        self._initial_visibility = visible

        # Gradio state
        self.component_id: gr.Number
        self.visible: gr.Number
        self.gr_component = gr.Box
        self.output: gr.Textbox

    @abstractmethod
    def _render(self, id_: int, visible: bool):
        ...

    def render(self) -> None:
        self.component_id = gr.Number(value=self._id, visible=False)
        self.visible = gr.Number(int(self._initial_visibility), visible=False)
        self.gr_component = self._render(self._id, self._initial_visibility)


class Input(Component):
    vname = "v"

    def _render(self, id_: int, visible: bool) -> gr.Textbox:
        self.output = gr.Textbox(
            label=f"Input: {{{self.vname}{id_}}}",
            interactive=True,
            placeholder="Variable value",
            visible=visible,
        )
        return self.output


class TaskComponent(Component, ABC):
    vname = "t"

    def __init__(self, id_: int, visible: bool = False):
        super().__init__(id_, visible)
        self.name: str
        self.input: gr.Textbox

    @abstractmethod
    def execute(self, input):
        ...


class AITask(TaskComponent):
    name = "AI Task"

    def _render(self, id_: int, visible: bool) -> gr.Box:
        with gr.Box(visible=visible) as gr_component:
            gr.Markdown(
                f"""
            {self.name}
            <br> Use this Task to give instructions to ChatGPT.
            """
            )
            with gr.Row():
                self.input = gr.Textbox(
                    label="Instructions",
                    lines=10,
                    interactive=True,
                    placeholder="Example - summarize this text: {v1}",
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

    def _render(self, id_: int, visible: bool) -> gr.Box:
        with gr.Box(visible=visible) as gr_component:
            gr.Markdown(
                f"""
            {self.name}
            <br> Use this Task to visit an URL and get its content.
            """
            )
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


class Task:
    available_tasks = [AITask, VisitURL]
    vname = "t"

    def __init__(self, id_: int):
        self._id = id_
        self._inner_tasks = [t(self._id, False) for t in self.available_tasks]

    def render(self) -> None:
        self.active_index = gr.Number(-1, visible=False)
        for t in self._inner_tasks:
            t.render()

    @property
    def component_id(self) -> gr.Textbox:
        return self._inner_tasks[0].component_id

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
        return [it.visible for t in all_tasks.values() for it in t._inner_tasks]

    @classmethod
    def active_indexes(cls) -> List[gr.Number]:
        return [t.active_index for t in all_tasks.values()]

    @classmethod
    def gr_components(cls) -> List[gr.Box]:
        return [it.gr_component for t in all_tasks.values() for it in t._inner_tasks]
