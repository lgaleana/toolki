import gradio as gr
from components import AITask, CodeTask

from examples import demo_buttons, demo_tasks


DEMO_ID = __name__
tasks = [
    CodeTask(
        0,
        "https://huggingface.co/",
        visible=True,
        code_value="Get text from a website. No html. No empty lines.",
    ),
    AITask(1, "Summarize: {t0}", visible=True),
]
demo_tasks[DEMO_ID] = tasks


def render():
    with gr.Tab("Example: Summarize a website"):
        demo_id = gr.Textbox(DEMO_ID, visible=False)
        tasks[0].render()
        tasks[1].render()
        demo_buttons(demo_id, tasks)
