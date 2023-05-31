import gradio as gr
from components import AITask, CodeTask

from examples import demo_buttons, demo_tasks


DEMO_ID = __name__
tasks = [
    CodeTask(
        0,
        "https://openai.com/",
        visible=True,
        code_value="Make a google search.",
    ),
    AITask(
        1,
        """Your goal is to create an ad for a website.
You will use an AI image generator to generate an image for your ad.

Here is the text from the website:
{t0}

Create a prompt for the AI image generator.
Avoid logos.""",
        visible=True,
    ),
    CodeTask(
        2,
        "{t1}",
        visible=True,
        code_value="Use openai key <put_your_key_in_here>. Generate an image from a prompt. Return the url.",
    ),
    AITask(
        1,
        """Here is the text from a website:
{t0}

Here is a prompt that was used by an AI image generator to generate an image for an ad:
{t1}

Consider the website content and the prompt to create a headline for an ad.""",
        visible=True,
    ),
]
demo_tasks[DEMO_ID] = tasks


def render():
    demo_id = gr.Textbox(DEMO_ID, visible=False)
    tasks[0].render()
    tasks[1].render()
    tasks[2].render()
    tasks[3].render()
    demo_buttons(demo_id, tasks)
