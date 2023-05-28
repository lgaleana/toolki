from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

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

    @abstractmethod
    def inputs(self) -> List:
        ...

    @property
    def _n_inputs(self) -> int:
        return len(self.inputs())

    def render(self) -> None:
        super().render()
        self.n_inputs = gr.Number(value=self._n_inputs, visible=False)

    @abstractmethod
    def execute(self, *vars, vars_in_scope: Dict[str, str]):
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
                self.prompt = gr.Textbox(
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

    def execute(self, prompt: str, vars_in_scope: Dict[str, str]) -> Optional[str]:
        if prompt:
            formatted_prompt = prompt.format(**vars_in_scope)
            print(f"Executing {self.name} with prompt :: {formatted_prompt}")
            return ai.llm.next([{"role": "user", "content": formatted_prompt}])

    def inputs(self) -> List[gr.Textbox]:
        return [self.prompt]


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
                self.url = gr.Textbox(
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

    def execute(self, url: str, vars_in_scope: Dict[str, str]) -> Optional[str]:
        if url:
            formatted_url = url.format(**vars_in_scope)
            print(f"Executing {self.name} with url :: {formatted_url}")
            return requests.get(formatted_url).text

    def inputs(self) -> List[gr.Textbox]:
        return [self.url]


class Task:
    available_tasks = [AITask, VisitURL]
    vname = "t"

    def __init__(self, id_: int):
        self._id = id_
        self._active_index = -1  # Nothing
        self._inner_tasks = [t(self._id, False) for t in self.available_tasks]

    def render(self) -> None:
        self.active_index = gr.Number(self._active_index, visible=False)
        for t in self._inner_tasks:
            t.render()

    @property
    def component_id(self) -> gr.Textbox:
        return self._inner_tasks[self._active_index].component_id

    @property
    def gr_component(self) -> gr.Box:
        return self._inner_tasks[self._active_index].gr_component

    @property
    def visible(self) -> gr.Number:
        return self._inner_tasks[self._active_index].visible

    @property
    def output(self) -> gr.Textbox:
        return self._inner_tasks[self._active_index].output

    @property
    def inputs(self) -> List[gr.Textbox]:
        return self._inner_tasks[self._active_index].inputs()

    @property
    def n_inputs(self) -> int:
        return self._inner_tasks[self._active_index].n_inputs

    def execute(self, *args):
        inner_task = self._inner_tasks[self._active_index]
        print(f"Executing {inner_task._source}: {inner_task._id}")
        return inner_task.execute(*args)


class State:
    MAX_TASKS = 10

    all_tasks = {i: Task(i) for i in range(MAX_TASKS)}

    @classmethod
    def task_visibilities(cls) -> List:
        return [it.visible for t in cls.all_tasks.values() for it in t._inner_tasks]

    @classmethod
    def task_rows(cls) -> List:
        return [
            it.gr_component for t in cls.all_tasks.values() for it in t._inner_tasks
        ] + [it.visible for t in cls.all_tasks.values() for it in t._inner_tasks]


tasks = State()
