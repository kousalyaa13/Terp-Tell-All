"""
web.py — Milestone 5 interface: a Gradio web UI for the RAG pipeline.

This is a thin UI on top of the end-to-end function `answer()` in app.py
(question -> retrieve -> grounded Groq answer -> cited sources). Run this for
the demo video; app.py still works as a command-line interface.

Run:
    python web.py
Then open http://localhost:7860
"""

import gradio as gr

from app import answer
from retrieval import build_index


def handle_query(question: str):
    """Run one question through the pipeline and return (answer, sources)."""
    if not question or not question.strip():
        return "Please type a question first.", ""
    result = answer(question)
    # result["sources"] items look like "  - Source 1: <name> (<url>)"
    sources = "\n".join("• " + s.strip(" -") for s in result["sources"])
    return result["answer"], sources


# Make sure the vector store is built before the UI accepts questions.
build_index()

with gr.Blocks(title="UMD CS Professor Review Guide") as demo:
    gr.Markdown(
        "# 🐢 UMD CS Professor Review Guide\n"
        "Ask about Computer Science professors and courses at the University of "
        "Maryland. Answers come **only** from real student reviews (PlanetTerp), "
        "and the reviews used are listed under *Retrieved from*.\n\n"
        "**Try:** *Which professor should I take for CMSC330?* · "
        "*How hard are Nelson Padua-Perez's exams?* · "
        "*What do students think of Clyde Kruskal for algorithms?*"
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Which professor do students recommend for CMSC330?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer_box = gr.Textbox(label="Answer", lines=8)
    sources_box = gr.Textbox(label="Retrieved from (sources)", lines=4)

    gr.Examples(
        examples=[
            "Which professor do students recommend for CMSC330?",
            "How hard are Nelson Padua-Perez's exams in CMSC131 and CMSC132?",
            "What do students think of Clyde Kruskal for CMSC351?",
            "Is CMSC216 a difficult course, and why?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
