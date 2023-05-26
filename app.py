import gradio as gr

import actions as a
from components import all_inputs, all_tasks


with gr.Blocks() as demo:
    # Initial layout
    gr.Markdown(
        """
    # Toolkit
    Define input variables to be used in your tasks.
    <br>Task outputs can be used in subsequent tasks.
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
        inputs=[i.visible for i in all_tasks.values()],
        outputs=[i.gr_component for i in all_tasks.values()]  # type: ignore
        + [i.visible for i in all_tasks.values()],
    )
    remove_task_btn.click(
        a.remove_task,
        inputs=[i.visible for i in all_tasks.values()],
        outputs=[i.gr_component for i in all_tasks.values()]  # type: ignore
        + [i.visible for i in all_tasks.values()],
    )

    # Sequential execution
    execution_event = execute_btn.click(
        a._clear_error, inputs=[], outputs=[error_message]
    )
    for i, task in all_tasks.items():
        execution_event = execution_event.then(
            a.execute_task,
            inputs=[task.component_id, error_message, task.n_inputs] + task.inputs() + a._get_all_vars_up_to(i),  # type: ignore
            outputs=[task.output, error_message],
        )

demo.launch()
