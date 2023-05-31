import gradio as gr
from components import AITask, CodeTask

import examples.actions as ea


DEMO_ID = "hello"
tasks = [
    CodeTask(
        0,
        "https://openai.com/",
        visible=True,
        code_value="Get text from a website (no html). No empty lines.",
    ),
    AITask(1, "Summarize: {t0}", visible=True),
]
ea.demo_tasks[DEMO_ID] = tasks


def render():
    demo_id = gr.Textbox(DEMO_ID, visible=False)
    tasks[0].render()
    tasks[1].render()
    error_message = gr.HighlightedText(value=None, visible=False)
    execute_btn = gr.Button("Execute")

    # Sequential execution
    execution_event = execute_btn.click(
        # Clear error message
        lambda: gr.HighlightedText.update(value=None, visible=False),
        inputs=[],
        outputs=[error_message],
    )
    prev_tasks = []
    for task in tasks:
        execution_event = execution_event.then(
            ea.execute_task,
            inputs=[demo_id, task.component_id, error_message]
            + task.inputs
            + [t.output for t in prev_tasks],
            outputs=[task.output, error_message],
        )
        prev_tasks.append(task)
