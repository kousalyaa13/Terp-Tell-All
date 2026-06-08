"""
retrieval.py — Milestone 4: embedding + vector store + retrieval.

What it does:
    1. EMBED  : load the all-MiniLM-L6-v2 model (runs locally, no API key) and
                embed every chunk from data/chunks.jsonl.
    2. STORE  : load the chunks + embeddings into a persistent ChromaDB
                collection, with metadata for each chunk (source document name,
                position in that document, professor, course, rating) so the
                source can be shown later for attribution.
    3. RETRIEVE: retrieve(query, k) embeds the query and returns the top-k most
                similar chunks with their source info and distance scores.
    4. TEST   : run several evaluation-plan questions and print the results.

Run:
    python retrieval.py            # builds the index if needed, then tests
    python retrieval.py --rebuild  # force re-embedding from scratch
"""

import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
CHUNKS_PATH = ROOT / "data" / "chunks.jsonl"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "umd_cs_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_K = 5

# Load the embedding model once at import time (used for both indexing + queries).
print(f"Loading embedding model: {MODEL_NAME} ...")
_model = SentenceTransformer(MODEL_NAME)
_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def _load_chunks() -> list[dict]:
    return [json.loads(line) for line in CHUNKS_PATH.open(encoding="utf-8")]


# =============================================================================
# 1 + 2. EMBED and STORE
# =============================================================================
def build_index(rebuild: bool = False):
    """Embed all chunks and load them into ChromaDB with metadata."""
    if rebuild:
        try:
            _client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    # Use cosine distance: 0.0 = identical meaning, higher = less similar.
    collection = _client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    chunks = _load_chunks()
    if collection.count() == len(chunks) and not rebuild:
        print(f"Index already built ({collection.count()} chunks). "
              f"Use --rebuild to redo.")
        return collection

    print(f"Embedding {len(chunks)} chunks with {MODEL_NAME} ...")
    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(
        texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True
    ).tolist()

    # Metadata: source document name + position in that document (for attribution),
    # plus professor/course/rating so answers can be filtered or cited.
    position_in_source: dict[str, int] = {}
    ids, metadatas = [], []
    for c in chunks:
        src = c["source"]
        pos = position_in_source.get(src, 0)
        position_in_source[src] = pos + 1
        ids.append(c["id"])
        metadatas.append(
            {
                "source": src,
                "source_url": c["source_url"],
                "position_in_source": pos,
                "professor": c["professor"] or "n/a",
                "course": c["course"] or "n/a",
                "rating": c["rating"] if isinstance(c["rating"], int) else -1,
            }
        )

    # Add in batches (ChromaDB caps how many items you can add at once).
    BATCH = 1000
    for i in range(0, len(ids), BATCH):
        sl = slice(i, i + BATCH)
        collection.add(
            ids=ids[sl],
            documents=texts[sl],
            embeddings=embeddings[sl],
            metadatas=metadatas[sl],
        )
    print(f"Stored {collection.count()} chunks in ChromaDB at {CHROMA_DIR.name}/")
    return collection


def _get_collection():
    return _client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


# =============================================================================
# 3. RETRIEVE
# =============================================================================
def retrieve(query: str, k: int = DEFAULT_K) -> list[dict]:
    """Return the top-k most relevant chunks for a query, with source + distance.

    Each result has: text, distance (0 = identical, lower = more relevant),
    source, professor, course, position_in_source.
    """
    collection = _get_collection()
    q_emb = _model.encode([query], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append(
            {
                "text": doc,
                "distance": dist,
                "source": meta["source"],
                "source_url": meta.get("source_url", ""),
                "professor": meta["professor"],
                "course": meta["course"],
                "position_in_source": meta["position_in_source"],
            }
        )
    return results


# =============================================================================
# 4. TEST
# =============================================================================
# The 5 questions from planning.md -> Evaluation Plan.
TEST_QUERIES = [
    "What do students say about the difficulty of Nelson Padua-Perez's exams in CMSC131 and CMSC132?",
    "Which professor do students recommend for CMSC330?",
    "What do students think of Clyde Kruskal as a professor for CMSC351 (Algorithms)?",
    "Do students consider CMSC216 a hard course, and why?",
    "Do students agree in their opinion of Nelson Padua-Perez?",
]

RATINGS_PATH = ROOT / "data" / "retrieval_ratings.md"


def show_query(query: str, k: int = DEFAULT_K) -> list[dict]:
    """Print the top-k chunks for one query and return them."""
    print("\n" + "#" * 78)
    print(f"QUERY: {query}   (top-{k})")
    print("#" * 78)
    results = retrieve(query, k=k)
    for i, r in enumerate(results, 1):
        # Drop the metadata header line so you read the actual review text.
        preview = r["text"].split("\n", 1)[-1][:300].replace("\n", " ")
        print(f"\n[{i}] distance={r['distance']:.4f}  "
              f"prof={r['professor']}  course={r['course']}  "
              f"(source: {r['source']}, pos {r['position_in_source']})")
        print(f"    {preview}")
    return results


def _log_rating(query: str, rating: str, note: str):
    """Append a rating to data/retrieval_ratings.md for the README report."""
    label = {"g": "Good", "p": "Partial", "b": "Off-target"}.get(rating, rating)
    new_file = not RATINGS_PATH.exists()
    with RATINGS_PATH.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# Retrieval ratings\n\n| Question | Rating | Note |\n"
                    "|----------|--------|------|\n")
        f.write(f"| {query} | {label} | {note} |\n")
    print(f"  ...saved as '{label}' to {RATINGS_PATH.relative_to(ROOT)}")


def test_retrieval(k: int = DEFAULT_K):
    """Run all 5 evaluation-plan questions (no rating prompts)."""
    for q in TEST_QUERIES:
        show_query(q, k=k)


def ask_mode(k: int = DEFAULT_K):
    """Interactive: type a question, read the chunks, rate the retrieval.

    At the rating prompt enter:  g = good,  p = partial,  b = off-target,
    s = skip (don't log),  q = quit.
    """
    print("\nInteractive retrieval. Type a question (or 'q' to quit).")
    print("Tip: press Enter on a blank question to cycle through your 5 "
          "evaluation-plan questions.\n")
    preset = list(TEST_QUERIES)
    while True:
        query = input("\nQuestion> ").strip()
        if query.lower() in {"q", "quit", "exit"}:
            break
        if not query:                      # blank -> use next preset question
            if not preset:
                print("(no more preset questions)")
                continue
            query = preset.pop(0)
            print(f"(using evaluation question) {query}")

        show_query(query, k=k)

        rating = input(
            "\nRate this retrieval [g=good / p=partial / b=off-target / "
            "s=skip / q=quit]: "
        ).strip().lower()
        if rating in {"q", "quit"}:
            break
        if rating == "s" or rating not in {"g", "p", "b"}:
            print("  ...not logged")
            continue
        note = input("Optional note (why?): ").strip()
        _log_rating(query, rating, note)

    print(f"\nDone. Ratings saved in {RATINGS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--rebuild"]
    build_index(rebuild="--rebuild" in sys.argv)

    if "--ask" in args:                    # interactive + rating mode
        ask_mode()
    elif args:                             # one-off question from the command line
        show_query(" ".join(args))
    else:                                  # default: run all 5 eval questions
        test_retrieval()
