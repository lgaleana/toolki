import gradio as gr

demo = None

def component():
    with gr.Row():
        gr.Textbox("Hello")
        gr.Textbox("World")


with gr.Blocks() as demo:
    for c in [component, component]:
        c()
    gr.Button("Hey")

print("heyhey")
with gr.Blocks() as demo:
    for c in [component, component]:
        c()
    gr.Textbox("World")

demo.launch()