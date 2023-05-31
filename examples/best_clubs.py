import gradio as gr
from components import AITask, CodeTask

from examples import demo_buttons, demo_tasks


DEMO_ID = __name__
tasks = [
    CodeTask(
        0,
        "nightlife in NYC",
        visible=True,
        code_value="Make a google search.",
    ),
    CodeTask(
        1,
        "{t0}",
        visible=True,
        code_value="Get the main content from a list of urls. Top 5. No html. No empty lines. Include only the first 3000 characters. Use the correct headers.",
    ),
    AITask(
        2,
        """Here is the content from a list of websites:
{t1}

What is the overal topic?
Extract the most relevant points.""",
        visible=True,
    ),
]
demo_tasks[DEMO_ID] = tasks


def render():
    with gr.Tab("Example: Nightlife in NYC"):
        demo_id = gr.Textbox(DEMO_ID, visible=False)
        tasks[0].render()
        tasks[1].render()
        tasks[2].render()
        demo_buttons(demo_id, tasks)
