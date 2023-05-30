import gradio as gr

from components import Task

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
