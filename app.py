import gradio as gr

import actions as a
from components import AITask, all_inputs, all_tasks, VisitURL


def _get_all_vars_up_to(to: int):
    return [in_.output for in_ in all_inputs.values()] + [
        t.output for i, t in all_tasks.items() if i < to
    ]


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
    for i in all_inputs.values():
        i.render()
    with gr.Row():
        add_input_btn = gr.Button("Add input variable")
        remove_input_btn = gr.Button("Remove input variable")
    for t in all_tasks.values():
        t.render()
    task_picker = gr.Dropdown(
        [AITask.NAME, VisitURL.NAME],
        value=AITask.NAME,
        label="Pick a new Task",
        type="index",
    )
    with gr.Row():
        add_task_btn = gr.Button("Add task")
        remove_task_btn = gr.Button("Remove task")
    error_message = gr.HighlightedText(value=None, visible=False)
    execute_btn = gr.Button("Execute")

    # Edit layout
    add_input_btn.click(
        a.add_input,
        inputs=[i.visible for i in all_inputs.values()],
        outputs=[i.gr_component for i in all_inputs.values()]  # type: ignore
        + [i.visible for i in all_inputs.values()],
    )
    remove_input_btn.click(
        a.remove_input,
        inputs=[i.visible for i in all_inputs.values()],
        outputs=[i.gr_component for i in all_inputs.values()]  # type: ignore
        + [i.visible for i in all_inputs.values()],
    )
    add_task_btn.click(
        a.add_task,
        inputs=[task_picker] + [v for t in all_tasks.values() for v in t.visibilities],  # type: ignore
        outputs=[c for t in all_tasks.values() for c in t.gr_components]  # type: ignore
        + [v for t in all_tasks.values() for v in t.visibilities],
    )
    remove_task_btn.click(
        a.remove_task,
        inputs=[v for t in all_tasks.values() for v in t.visibilities],  # type: ignore
        outputs=[c for t in all_tasks.values() for c in t.gr_components]  # type: ignore
        + [v for t in all_tasks.values() for v in t.visibilities],
    )

    # Sequential execution
    execution_event = execute_btn.click(
        lambda _: gr.HighlightedText.update(value=None, visible=False),
        inputs=[],
        outputs=[error_message],
    )
    for i, task in all_tasks.items():
        execution_event = execution_event.then(
            a.execute_task,
            inputs=[task.component_id, error_message, task.n_inputs]
            + task.inputs
            + _get_all_vars_up_to(i),
            outputs=[task.output, error_message],
        )

demo.launch()
