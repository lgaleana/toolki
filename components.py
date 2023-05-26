from typing import Dict, Optional, Union

import gradio as gr

import ai


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


MAX_INPUTS = 10
MAX_TASKS = 10


all_inputs = {i: Component(i, Input()) for i in range(MAX_INPUTS)}
all_tasks = {i: Component(i, AITask()) for i in range(MAX_TASKS)}

all_inputs[0]._initial_visibility = True
all_tasks[0]._initial_visibility = True
