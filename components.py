import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

import gradio as gr

import ai


class Component(ABC):
    def __init__(self, id_: int):
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
        self._source = self.__class__.__name__

    def render(self, id_: int) -> None:
        self.gr_component = self._render(id_)

    @property
    @abstractmethod
    def inputs(self) -> List[gr.Textbox]:
        ...

    @property
    def n_inputs(self) -> int:
        return len(self.inputs)

    @abstractmethod
    def _render(self, id_) -> gr.Box:
        ...

    @abstractmethod
    def execute(self, *args, vars_in_scope: Dict[str, Any]):
        ...


class AITask(TaskComponent):
    name = "AI Task"

    def _render(self, id_: int) -> gr.Box:
        with gr.Box(visible=False) as gr_component:
            with gr.Row():
                self.input = gr.Textbox(
                    label="Instructions",
                    lines=10,
                    interactive=True,
                    placeholder="What would you like ChatGPT to do?",
                )
                self.output = gr.Textbox(
                    label=f"Output: {{{self.vname}{id_}}}",
                    lines=10,
                    interactive=True,
                )
            return gr_component

    @property
    def inputs(self) -> List[gr.Textbox]:
        return [self.input]

    def execute(self, prompt: str, vars_in_scope: Dict[str, Any]) -> str:
        formatted_prompt = prompt.format(**vars_in_scope)
        return ai.llm.next([{"role": "user", "content": formatted_prompt}])


class CodeTask(TaskComponent):
    name = "Code Task"

    def _render(self, id_: int) -> gr.Column:
        with gr.Column(visible=False) as gr_component:
            code_prompt = gr.Textbox(
                label="What would you like to do?",
                interactive=True,
            )
            generate_code = gr.Button("Generate code")
            with gr.Row():
                with gr.Column():
                    with gr.Accordion(label="Generated code", open=False) as accordion:
                        raw_prompt_output = gr.Textbox(
                            label="Raw output",
                            lines=5,
                            interactive=True,
                        )
                        self.packages = gr.Textbox(
                            label="The following packages will be installed",
                            interactive=True,
                        )
                        self.function = gr.Textbox(
                            label="Code to be executed",
                            lines=10,
                            interactive=True,
                        )
                        error_message = gr.HighlightedText(value=None, visible=False)

                    self.input = gr.Textbox(
                        label="Input",
                        interactive=True,
                    )
                with gr.Column():
                    self.output = gr.Textbox(
                        label=f"Output: {{{self.vname}{id_}}}",
                        lines=10,
                        interactive=True,
                    )

            generate_code.click(
                self.generate_code,
                inputs=[code_prompt],
                outputs=[
                    raw_prompt_output,
                    self.packages,
                    self.function,
                    error_message,
                    accordion,
                ],
            )

        return gr_component

    @staticmethod
    def generate_code(code_prompt: str):
        import json

        raw_prompt_output = ""
        error_message = gr.HighlightedText.update(None, visible=False)
        accordion = gr.Accordion.update()

        if not code_prompt:
            return (
                raw_prompt_output,
                "",
                "",
                error_message,
                accordion,
            )

        print(f"Generating code.")
        parsed_output = {"packages": "", "script": ""}
        try:
            raw_prompt_output = ai.llm.next(
                [
                    {
                        "role": "user",
                        "content": f"""
                        Write a python function for the following request:
                        {code_prompt}

                        Do't save anything to disk. Instead, the function should return the necessary data.
                        Include all the necessary imports. Make sure that the package names are correct.
                        """,
                    }
                ],
                temperature=0,
            )

            raw_parsed_output = ai.llm.next(
                [
                    {
                        "role": "user",
                        "content": f"""
                        The following text has a python function with some imports that might need to be installed:
                        {raw_prompt_output}

                        Extract all the python packages that need to be installed with pip, nothing else.
                        Extract the function and the imports as a single python script, nothing else.

                        Write a JSON:
                        ```
                            {{
                                "packages": Python list of packages to be parsed with eval(). If no packages, the list should be empty.
                                "script": Python script to be executed with exec(). Include only the function and the imports.
                            }}
                        ```
                        """,
                    }
                ],
                temperature=0,
            )
            parsed_output = json.loads(
                re.search("({.*})", raw_parsed_output, re.DOTALL).group(1)
            )
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            error_message = gr.HighlightedText.update(
                value=[(str(e), "ERROR")], visible=True
            )
            accordion = gr.Accordion.update(open=True)
        return (
            raw_prompt_output,
            parsed_output["packages"],
            parsed_output["script"].replace("```python", "").replace("```", ""),
            error_message,
            accordion,
        )

    @property
    def inputs(self) -> List[gr.Textbox]:
        return [self.packages, self.function, self.input]

    def execute(
        self, packages: str, function: str, input: str, vars_in_scope: Dict[str, Any]
    ):
        import subprocess
        import sys

        for p in eval(packages):
            subprocess.check_call([sys.executable, "-m", "pip", "install", p])
        exec(function, locals())
        # Should be last function in scope
        self._toolkit_func = list(locals().items())[-1][1]

        formatted_input = input.format(**vars_in_scope)
        try:
            formatted_input = eval(formatted_input)
        except:
            pass
        return self._toolkit_func(formatted_input)


class Task(Component):
    available_tasks = [AITask, CodeTask]
    vname = "t"

    def __init__(self, id_: int):
        super().__init__(id_)
        self._inner_tasks = [t() for t in self.available_tasks]
        self.gr_component: gr.Box

    def _render(self, id_: int) -> gr.Box:
        with gr.Box(visible=False) as gr_component:
            self.active_index = gr.Dropdown(
                [AITask.name, CodeTask.name],
                label="Pick a new Task",
                type="index",
            )
            for t in self._inner_tasks:
                t.render(id_)

            self.active_index.select(
                self.pick_task,
                inputs=[self.active_index],
                outputs=[t.gr_component for t in self._inner_tasks],
            )
        return gr_component

    @staticmethod
    def pick_task(idx: int) -> List[Dict]:
        update = [gr.Box.update(visible=False)] * len(Task.available_tasks)
        update[idx] = gr.Box.update(visible=True)
        return update

    @property
    def inputs(self) -> List[gr.Textbox]:
        return [i for t in self._inner_tasks for i in t.inputs]

    @property
    def outputs(self) -> List[gr.Textbox]:
        return [t.output for t in self._inner_tasks]

    @property
    def inner_n_inputs(self) -> List[int]:
        return [t.n_inputs for t in self._inner_tasks]

    def execute(self, active_index, *args, vars_in_scope: Dict[str, Any]):
        inner_task = self._inner_tasks[active_index]
        print(f"Executing {self._source}: {self._id}")
        return inner_task.execute(*args, vars_in_scope)


MAX_TASKS = 10

all_tasks = {i: Task(i) for i in range(MAX_TASKS)}


class Tasks:
    @classmethod
    def visibilities(cls) -> List[gr.Number]:
        return [t.visible for t in all_tasks.values()]

    @classmethod
    def active_indexes(cls) -> List[gr.Dropdown]:
        return [t.active_index for t in all_tasks.values()]

    @classmethod
    def gr_components(cls) -> List[gr.Box]:
        return [t.gr_component for t in all_tasks.values()]
