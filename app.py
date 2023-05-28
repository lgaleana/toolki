import gradio as gr

import actions as a
from components import AITask, State as s, VisitURL


def _get_all_vars_up_to(to: int):
    return [t.output for i, t in s.all_tasks.items() if i < to]


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
    for t in s.all_tasks.values():
        t.render()
    task_picker = gr.Dropdown(
        [AITask.name, VisitURL.name],
        value=AITask.name,
        label="Pick a new Task",
        type="index",
    )
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")
    error_message = gr.HighlightedText(value=None, visible=False)
    execute_btn = gr.Button("Execute")

    # Edit layout
    add_task_btn.click(
        a.add_task,
        inputs=[task_picker] + s.task_visibilities(),  # type: ignore
        outputs=s.task_rows(),
    )
    remove_task_btn.click(
        a.remove_task, inputs=s.task_visibilities(), outputs=s.task_rows()
    )

    # Sequential execution
    execution_event = execute_btn.click(
        lambda: gr.HighlightedText.update(value=None, visible=False),
        inputs=[],
        outputs=[error_message],
    )
    for i, task in s.all_tasks.items():
        execution_event = execution_event.then(
            a.execute_task,
            inputs=[task.component_id, error_message, task.n_inputs]
            + task.inputs
            + _get_all_vars_up_to(i),
            outputs=[task.output, error_message],
        )

demo.launch()
