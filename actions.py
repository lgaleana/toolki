import gradio as gr

from components import MAX_TASKS, all_tasks, Task


def add_task(*visibilities):
    for i, visible in enumerate(visibilities, 1):
        if not bool(visible):
            return (
                [gr.Box.update(visible=True)] * i
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i)
                + [1] * i
                + [0] * (MAX_TASKS - i)
            )
    return [gr.Box.update()] * MAX_TASKS + [gr.Number.update()] * MAX_TASKS


def remove_task(*visibilities):
    for i, visible in reversed(list(enumerate(visibilities))):
        if bool(visible):
            return (
                [gr.Box.update(visible=True)] * i
                + [gr.Box.update(visible=False)] * (MAX_TASKS - i)
                + [1] * i
                + [0] * (MAX_TASKS - i)
            )
    return [gr.Box.update()] * MAX_TASKS + [gr.Number.update()] * MAX_TASKS


def execute_task(task_id: int, active_index: int, error_value, *args):
    """
    Params:
        - task_id: This will tell us which task to execute.
        - active_index: The index of the actual task that is visible.
        - error_value: I carry around whether there is an error in the execution, to be displayed at the end.
        - args: Other variables that will be decomposed.
    """
    n_avail_tasks = len(Task.available_tasks)
    outputs = [
        ""
    ] * n_avail_tasks  # We need to return outputs for all tasks in the row.
    error_update = gr.HighlightedText.update(
        value=error_value, visible=error_value is not None
    )

    # If not task has been picked or if ther has been an error, skip.
    if active_index is None or error_value:  # Active index could be 0
        return outputs + [error_update]

    task_id = int(task_id)
    active_index = int(active_index)
    inner_n_inputs = all_tasks[task_id].inner_n_inputs

    # Decompose args
    # - start_inputs: Where the active task inputs start within args.
    # - end_inputs: End of the active task inputs.
    # - task_inputs: The active task inputs.
    # - all_active_indexes: Indexes of the active tasks in the other tasks.
    # - all_task_outputs: Outputs of every other task.
    start_inputs = 0
    end_inputs = 0
    end_all_inputs = sum(inner_n_inputs)
    for i, n in enumerate(inner_n_inputs):
        if i == active_index:
            end_inputs = start_inputs + n
            break
        start_inputs += n
    task_inputs = args[start_inputs:end_inputs]
    all_active_indexes = args[end_all_inputs : end_all_inputs + MAX_TASKS]
    all_task_outputs = args[end_all_inputs + MAX_TASKS :]

    # If no inputs, skip
    non_empty_inputs = [i for i in task_inputs if i]
    if not non_empty_inputs:
        return outputs + [error_update]

    # Put task outputs in a dictionary with names.
    vars_in_scope = {}
    for i, other_active_index in enumerate(all_active_indexes):
        if other_active_index is not None:
            vars_in_scope[f"{Task.vname}{i}"] = all_task_outputs[
                i * n_avail_tasks + int(other_active_index)
            ]

    try:
        # Task logic gets inserted into the right index
        outputs[active_index] = all_tasks[task_id].execute(
            active_index, *task_inputs, vars_in_scope=vars_in_scope
        )
        return outputs + [error_update]
    except Exception as e:
        import traceback

        traceback.print_exc()
        outputs[active_index] = f"ERROR :: {e}"
        return outputs + [
            gr.HighlightedText.update(
                value=[(f"Error in Task {task_id} :: {e}", "ERROR")],
                visible=True,
            )
        ]
