import gradio as gr

import actions as a
from examples import summarize_website
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
    <br>**Code Task**: ChatGPT will create a python function to do something for you. Eg, get the text from a website.
    <br> Use this task for things that ChatGPT can't do on its own, like access the internet or iterate over 4K+ tokens.
    <br>
    <br>Output from previous tasks can be referenced in subsequen tasks with {tn}. Max 10 tasks allowed (for now).
    """
    )
    with gr.Tab("Toolkit"):
        for t in all_tasks.values():
            t.render()
        with gr.Row():
            add_task_btn = gr.Button("Add task")
            remove_task_btn = gr.Button("Remove task")
        error_message = gr.HighlightedText(value=None, visible=False)
        execute_btn = gr.Button("Execute")

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
        prev_tasks = []
        for i, task in all_tasks.items():
            execution_event = execution_event.then(
                a.execute_task,
                inputs=[task.component_id, task.active_index, error_message]
                + task.inputs
                + [t.active_index for t in prev_tasks]
                + [o for t in prev_tasks for o in t.outputs],
                outputs=task.outputs + [error_message],
            )
            prev_tasks.append(task)
    with gr.Tab("Example: Summarize website"):
        summarize_website.render()

demo.launch()
