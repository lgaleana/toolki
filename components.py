import json
import re
import traceback
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

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
        self.gr_component = self._render()

    @abstractmethod
    def _render(self) -> Union[gr.Box, gr.Textbox]:
        ...


class Input(Component):
    vname = "v"

    def _render(self) -> gr.Textbox:
        self.output = gr.Textbox(
            label=f"Input: {{{self.vname}{self._id}}}",
            interactive=True,
            placeholder="Variable value",
            visible=False,
        )
        return self.output


class TaskComponent(Component, ABC):
    vname = "t"

    def __init__(self, id_: int, value: str = "", visible: bool = False):
        super().__init__(id_)
        self._initial_value = value
        self._initial_visbility = visible
        self.name: str
        self.input: gr.Textbox

    def format_input(self, input: str, vars_in_scope: Dict[str, Any]) -> str:
        try:
            json.loads(input)
            return input
        except:
            input = input.strip()
            prompt_vars = [v for v in re.findall("{(.*)}", input)]
            undefined_vars = prompt_vars - vars_in_scope.keys()
            if len(undefined_vars) > 0:
                raise KeyError(
                    f"The variables :: {undefined_vars} in task :: {self._id} are being used before being defined."
                )
            return input.format(**vars_in_scope)

    @property
    def n_inputs(self) -> int:
        return len(self.inputs)

    @property
    @abstractmethod
    def inputs(self) -> List[gr.Textbox]:
        ...

    @abstractmethod
    def execute(self, *args, vars_in_scope: Dict[str, Any]):
        ...


class AITask(TaskComponent):
    name = "AI Task"

    def _render(self) -> gr.Box:
        with gr.Box(visible=self._initial_visbility) as gr_component:
            with gr.Row():
                self.input = gr.Textbox(
                    label="Instructions",
                    lines=10,
                    interactive=True,
                    placeholder="What would you like ChatGPT to do?",
                    value=self._initial_value,
                )
                self.output = gr.Textbox(
                    label=f"Output: {{{self.vname}{self._id}}}",
                    lines=10,
                    interactive=True,
                )
            return gr_component

    @property
    def inputs(self) -> List[gr.Textbox]:
        return [self.input]

    def execute(self, prompt: str, vars_in_scope: Dict[str, Any]) -> Optional[str]:
        formatted_prompt = self.format_input(prompt, vars_in_scope)
        if formatted_prompt:
            return ai.llm.next([{"role": "user", "content": formatted_prompt}])


class CodeTask(TaskComponent):
    name = "Code Task"

    def __init__(
        self, id_: int, value: str = "", visible: bool = False, code_value: str = ""
    ):
        super().__init__(id_, value, visible)
        self._initial_code_value = code_value

    def _render(self) -> gr.Box:
        with gr.Box(visible=self._initial_visbility) as gr_component:
            with gr.Row():
                with gr.Column():
                    self.code_prompt = gr.Textbox(
                        label="What would you like the code to do?",
                        interactive=True,
                        value=self._initial_code_value,
                        lines=3,
                    )
                    generate_code = gr.Button("Generate code")
                    with gr.Accordion(label="Generated code", open=False) as accordion:
                        self.accordion = accordion
                        self.raw_output = gr.Textbox(
                            label="Raw output",
                            lines=5,
                            interactive=False,
                        )
                        self.packages = gr.Textbox(
                            label="The following packages will be installed",
                            interactive=True,
                        )
                        self.script = gr.Textbox(
                            label="Code to be executed",
                            lines=10,
                            interactive=True,
                        )
                        self.error_message = gr.HighlightedText(
                            value=None, visible=False
                        )

                    self.input = gr.Textbox(
                        label="Input", interactive=True, value=self._initial_value
                    )
                with gr.Column():
                    self.output = gr.Textbox(
                        label=f"Output: {{{self.vname}{self._id}}}",
                        lines=14,
                        interactive=True,
                    )

            generate_code.click(
                self.generate_code,
                inputs=[self.code_prompt],
                outputs=[
                    self.raw_output,
                    self.packages,
                    self.script,
                    self.error_message,
                    self.accordion,
                ],
            )

        return gr_component

    @staticmethod
    def generate_code(code_prompt: str):
        raw_output = ""
        packages = ""
        script = ""
        error_message = gr.HighlightedText.update(None, visible=False)
        accordion = gr.Accordion.update()

        if not code_prompt:
            return (
                raw_output,
                packages,
                script,
                error_message,
                accordion,
            )

        def llm_call(prompt):
            return ai.llm.next([{"role": "user", "content": prompt}], temperature=0)

        print(f"Generating code.")
        try:
            raw_output = llm_call(
                f"""Write a python function to:
                {code_prompt}

Write the code for the function. Name the function toolkit.
Use pip packages where available.
Include the necessary imports.
Instead of printing or saving to disk, the function should return the data."""
            )
            with ThreadPoolExecutor() as executor:
                packages, script = tuple(
                    executor.map(
                        llm_call,
                        [
                            f"""The following text has some python code:
{raw_output}

Find the pip packages that need to be installed and get their corresponsing names in pip.
Package names in the imports and in pip might be different. Use the correct pip names.
Include only the packages that need to be installed with pip.
                            
Put them in a valid JSON:
```
{{
    "packages": List of packages. If no packages, empty list.
}}
```""",
                            f"""The following text has some python code:
{raw_output}

Extract it. Remove anything after the function definition.""",
                        ],
                    )
                )
            for packages in re.findall("{.*}", packages, re.DOTALL):
                try:
                    packages = json.loads(packages)
                    packages = packages["packages"]
                except:
                    print(packages)
                    traceback.print_exc()
                    packages = "ERROR"
        except Exception as e:
            traceback.print_exc()
            error_message = gr.HighlightedText.update(
                value=[(str(e), "ERROR")], visible=True
            )
            accordion = gr.Accordion.update(open=True)
        return (
            raw_output,
            packages,
            script.replace("```python", "").replace("```", "").strip(),
            error_message,
            accordion,
        )

    @property
    def inputs(self) -> List[gr.Textbox]:
        return [self.packages, self.script, self.input]

    def execute(
        self, packages: str, script: str, input: str, vars_in_scope: Dict[str, Any]
    ):
        if not script:
            return None
        script = script.strip()

        formatted_input = self.format_input(input, vars_in_scope)

        import inspect
        import subprocess
        import sys

        def run(toolkit_func):
            if len(inspect.getfullargspec(toolkit_func)[0]) > 0:
                if formatted_input:
                    try:
                        return toolkit_func(eval(formatted_input))
                    except:
                        return toolkit_func(formatted_input)
                raise ValueError(f"Code for task :: {self._id} needs an input.")
            return toolkit_func()

        for p in eval(packages):
            subprocess.check_call([sys.executable, "-m", "pip", "install", p])

        script = f"import os\nos.environ = {{}}\n\n{script}"
        exec(script, locals())

        locals_ = locals()
        if "toolkit" in locals_:
            toolkit_func = locals_["toolkit"]
            return run(toolkit_func)
        for var in reversed(locals_.values()):
            # Try to run all local functions
            if callable(var):
                try:
                    return run(var)
                except:
                    continue
        raise RuntimeError(f"Unable to run the code for task :: {self._id}")


class Task(Component):
    available_tasks = [AITask, CodeTask]
    vname = "t"

    def __init__(self, id_: int):
        super().__init__(id_)
        self._inner_tasks = [t(id_) for t in self.available_tasks]
        self.gr_component: gr.Box

    def _render(self) -> gr.Box:
        with gr.Box(visible=False) as gr_component:
            self.active_index = gr.Dropdown(
                [AITask.name, CodeTask.name],
                label="Pick a new Task",
                type="index",
            )
            for t in self._inner_tasks:
                t.render()

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
