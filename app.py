import gradio as gr

import actions as a
from examples import (
    authenticate_google,
    best_clubs,
    generate_ad,
    seo,
    summarize_website,
)
from components import all_tasks, Tasks


with gr.Blocks() as demo:
    # Initial layout
    gr.Markdown(
        """
    # Toolkit
    Assemble tasks to build an E2E application with everyday language.
    <br>There are 2 types of tasks.
    <br>
    <br>**AI Task**: Ask ChatGPT to do something for you. Eg, summarize a text.
    <br>**Code Task**: You will need code to do certain things that ChatGPT can't do, like access the internet or iterate over 4k+ tokens.
    <br> With this task, ChatGPT will generate code and then execute it. The code must be generated before executing all tasks.
    <br>
    <br>Output from other tasks can be referenced in the current task with {tn}. Max 10 tasks allowed (for now).
    """
    )
    with gr.Tab("Toolkit"):
        for t in all_tasks.values():
            t.render()
        with gr.Row():
            add_task_btn = gr.Button("Add task")
            remove_task_btn = gr.Button("Remove task")
        error_message = gr.HighlightedText(value=None, visible=False)
        execute_btn = gr.Button("Execute tasks")

        # Edit layout
        add_task_btn.click(
            a.add_task,
            inputs=Tasks.visibilities(),
            outputs=Tasks.gr_components() + Tasks.visibilities(),
        )
        remove_task_btn.click(
            a.remove_task,
            inputs=Tasks.visibilities(),
            outputs=Tasks.gr_components() + Tasks.visibilities(),
        )

        # Sequential execution
        execution_event = execute_btn.click(
            # Clear error message
            lambda: gr.HighlightedText.update(value=None, visible=False),
            inputs=[],
            outputs=[error_message],
        )
        for i, task in all_tasks.items():
            execution_event = execution_event.then(
                a.execute_task,
                inputs=[task.component_id, task.active_index, error_message]
                + task.inputs
                + [t.active_index for t in all_tasks.values() if t != task]
                + [o for t in all_tasks.values() if t != task for o in t.outputs],
                outputs=task.outputs + [error_message],
            )

    # Examples
    summarize_website.render()
    seo.render()
    best_clubs.render()
    generate_ad.render()
    authenticate_google.render()

demo.launch()
