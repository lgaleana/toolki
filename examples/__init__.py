from typing import List
import gradio as gr

from components import Task, TaskComponent


def demo_buttons(demo_id, tasks: List[TaskComponent]):
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
            execute_task,
            inputs=[demo_id, task.component_id, error_message]
            + task.inputs
            + [t.output for t in prev_tasks],
            outputs=[task.output, error_message],
        )
        prev_tasks.append(task)


demo_tasks = {}


def execute_task(demo_id: str, task_id: int, error_value, *args):
    error_update = gr.HighlightedText.update(
        value=error_value, visible=error_value is not None
    )

    if error_value:
        return ["", error_update]

    task_id = int(task_id)
    n_inputs = demo_tasks[demo_id][task_id].n_inputs

    task_inputs = args[:n_inputs]
    prev_task_outputs = args[n_inputs:]

    non_empty_inputs = [i for i in task_inputs if i]
    if not non_empty_inputs:
        return ["", error_update]

    # Put task outputs in a dictionary with names.
    vars_in_scope = {f"{Task.vname}{i}": o for i, o in enumerate(prev_task_outputs)}

    try:
        # Task logic gets inserted into the right index
        output = demo_tasks[demo_id][task_id].execute(
            *task_inputs, vars_in_scope=vars_in_scope
        )
        return [output, error_update]
    except Exception as e:
        import traceback

        print(traceback.format_tb(e.__traceback__))
        return [
            "ERROR",
            gr.HighlightedText.update(
                value=[(f"Error in Task {task_id} :: {e}", "ERROR")],
                visible=True,
            ),
        ]
