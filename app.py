import gradio as gr

import actions as a
from components import all_tasks, Tasks


with gr.Blocks() as demo:
    # Initial layout
    gr.Markdown(
        """
    # Toolkit
    Define input variables to be used in your tasks.
    <br>Task outputs can be used in subsequent tasks.
    <br>5 input variables and 10 tasks allowed (for now).
    <br>
    <br>AI tasks call into ChatGPT to perform actions.
    <br>Chain inputs and tasks to build an E2E application.
    <br>
    <br>Example prompt: "Translate the following text into spanish and add {v0} more sentences: {t0}".
    """
    )
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
            + task.inputs()
            + [t.active_index for t in prev_tasks]
            + [o for t in prev_tasks for o in t.outputs()],
            outputs=task.outputs() + [error_message],
        )
        prev_tasks.append(task)

demo.launch()
