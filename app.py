"""
app.py — Milestone 5: grounded generation + interface.

Pipeline (ties together Milestones 3-4):
    question -> retrieve(top-k chunks) -> build a grounded prompt -> Groq LLM
    -> answer that cites which reviews it used.

Grounding: the system prompt instructs the model to answer ONLY from the
retrieved reviews and to say it doesn't have enough information otherwise. Each
review is numbered in the context so the model can cite it as (Source N), and
the source documents are also appended programmatically after generation so the
attribution is always present even if the model forgets to cite.

Setup: put GROQ_API_KEY in .env (already present).

Run:
    python app.py                       # interactive question loop
    python app.py "your question here"  # one-off question
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from retrieval import retrieve, build_index, DEFAULT_K

load_dotenv()
MODEL = "llama-3.3-70b-versatile"          # Groq free-tier, OpenAI-compatible
_client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = (
    "You are a helpful guide to student reviews of Computer Science professors "
    "at the University of Maryland (UMD). Answer the question using ONLY the "
    "information in the provided reviews below. Do not use outside knowledge. "
    "If the reviews do not contain enough information to answer, reply exactly: "
    "\"I don't have enough information on that.\" "
    "When you state a fact, cite the review it came from using its number, like "
    "(Source 1). Keep the answer concise and base it on what multiple students "
    "say when possible."
)


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as a numbered list the model can cite."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        # The chunk text already starts with a metadata header; keep just the
        # review body for readability and add a clean, citable label.
        body = c["text"].split("\n", 1)[-1].strip()
        label = f"Source {i} — {c['source']}"
        if c["professor"] not in ("", "n/a"):
            label += f" (Prof: {c['professor']}, Course: {c['course']})"
        blocks.append(f"[{label}]\n{body}")
    return "\n\n".join(blocks)


def answer(question: str, k: int = DEFAULT_K) -> dict:
    """Retrieve, generate a grounded answer, and attach source attribution."""
    chunks = retrieve(question, k=k)
    context = build_context(chunks)

    user_prompt = (
        f"Reviews:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the reviews above, and cite sources like (Source N)."
    )

    completion = _client.chat.completions.create(
        model=MODEL,
        temperature=0.2,                   # low -> stay close to the reviews
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = completion.choices[0].message.content.strip()

    # Programmatic attribution: list the sources behind the retrieved chunks,
    # de-duplicated, so attribution is always shown.
    seen, sources = set(), []
    for i, c in enumerate(chunks, 1):
        key = (c["source"], c["source_url"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(f"  - Source {i}: {c['source']} ({c['source_url']})")

    return {"answer": text, "sources": sources, "chunks": chunks}


def print_answer(question: str, k: int = DEFAULT_K):
    result = answer(question, k=k)
    print("\n" + "=" * 78)
    print(f"Q: {question}")
    print("=" * 78)
    print(result["answer"])
    print("\nSources retrieved:")
    print("\n".join(result["sources"]))


def interactive():
    print("UMD CS Professor Review Guide. Ask a question (or 'q' to quit).")
    while True:
        q = input("\nQuestion> ").strip()
        if q.lower() in {"q", "quit", "exit"}:
            break
        if not q:
            continue
        print_answer(q)


if __name__ == "__main__":
    build_index()                          # ensure the vector store is ready
    args = sys.argv[1:]
    if args:
        print_answer(" ".join(args))
    else:
        interactive()
