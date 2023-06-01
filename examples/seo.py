import gradio as gr
from components import AITask, CodeTask

from examples import demo_buttons, demo_tasks


DEMO_ID = __name__
tasks = [
    CodeTask(
        0,
        "https://techcrunch.com",
        visible=True,
        code_value="Get the text from a website. Remove empty lines.",
    ),
    AITask(
        1,
        """Here is the text from a website:
{t0}

Analyze it and give me recommendations to optimize its SEO. Give the recommendations in the order of most impactful to least impactful.""",
        visible=True,
    ),
]
demo_tasks[DEMO_ID] = tasks


def render():
    with gr.Tab("Example: SEO recommendations"):
        demo_id = gr.Textbox(DEMO_ID, visible=False)
        with gr.Box():
            gr.Dropdown(
                value=CodeTask.name,
                label="Pick a new Task",
                interactive=False,
            )
            tasks[0].render()
        with gr.Box():
            gr.Dropdown(
                value=AITask.name,
                label="Pick a new Task",
                interactive=False,
            )
            tasks[1].render()
        demo_buttons(demo_id, tasks)
