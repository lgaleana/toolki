import gradio as gr
from components import AITask, CodeTask

from examples import demo_buttons, demo_tasks


DEMO_ID = __name__
tasks = [
    CodeTask(
        0,
        "{your json key in here} See: https://developers.google.com/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application",
        visible=True,
        code_value="Authenticate to read my google calendar. Return credentials as a json. I will provide the client secrets config in a json (not a file).",
    ),
    CodeTask(
        1,
        "{t0}",
        visible=True,
        code_value="Given a credentials json, get my calendar events of tomorrow.",
    ),
    AITask(
        2,
        """Here are the events in my calendar for tomorrow:
{t1}

Which hours of my day are free?""",
        visible=True,
    ),
]
demo_tasks[DEMO_ID] = tasks


def render():
    with gr.Tab("Example: Authenticate to google"):
        with gr.Box():
            demo_id = gr.Textbox(DEMO_ID, visible=False)
            gr.Dropdown(
                value=CodeTask.name,
                label="Pick a new Task",
                interactive=False,
            )
            tasks[0].render()
            gr.Dropdown(
                value=CodeTask.name,
                label="Pick a new Task",
                interactive=False,
            )
            tasks[1].render()
            gr.Dropdown(
                value=CodeTask.name,
                label="Pick a new Task",
                interactive=False,
            )
            tasks[2].render()
        demo_buttons(demo_id, tasks)
