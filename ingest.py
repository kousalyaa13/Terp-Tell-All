"""
ingest.py — Milestone 3: load documents, clean them, and produce chunks.

Pipeline:
    1. LOAD   : fetch reviews from the PlanetTerp public API (and any files you
                drop into documents/), and save the RAW data to documents/raw/
                in a consistent format BEFORE any cleaning.
    2. CLEAN  : strip HTML tags, unescape HTML entities (&amp;, &nbsp;, ...),
                normalize whitespace/newlines, and drop boilerplate. Each cleaned
                document is written to data/clean/ so you can read it.
    3. CHUNK  : one student review per chunk (my Chunking Strategy). If a review
                is longer than 800 characters it is split into 800-char pieces
                with a 50-char overlap. Each chunk keeps its professor/course
                context so an opinion is never separated from who it is about.
    4. INSPECT: print one cleaned document and one chunk so I can verify the
                cleaning worked before moving on to embedding (Milestone 4).

Run:  python ingest.py
Stdlib only — no pip install needed for this step.
"""

import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

# --- Chunking parameters (must match planning.md → Chunking Strategy) ---------
CHUNK_SIZE = 800       # characters; ~150 tokens; about the length of one review
CHUNK_OVERLAP = 50     # characters; only used when a long review must be split

# --- Folders ------------------------------------------------------------------
ROOT = Path(__file__).parent
RAW_DIR = ROOT / "documents" / "raw"        # raw, untouched source data
CLEAN_DIR = ROOT / "data" / "clean"          # cleaned, human-readable per source
MANUAL_DIR = ROOT / "documents"              # files you save here by hand
CHUNKS_PATH = ROOT / "data" / "chunks.jsonl" # final chunks (input to Milestone 4)

# --- PlanetTerp sources (from planning.md → Documents) ------------------------
# Course pages give reviews from every professor of that course; professor pages
# give a single professor's reviews across all their courses. Pulling both and
# de-duplicating gives broad coverage of UMD CS reviews.
PT_API = "https://planetterp.com/api/v1"
COURSES = ["CMSC131", "CMSC132", "CMSC216", "CMSC250", "CMSC330", "CMSC351"]
PROFESSORS = ["Nelson Padua-Perez", "Clyde Kruskal", "Anwar Mamat"]

USER_AGENT = "umd-cs-reviews-rag/0.1 (student project)"


# =============================================================================
# 1. LOAD
# =============================================================================
def fetch_json(endpoint: str, params: dict) -> dict | list:
    """GET a PlanetTerp API endpoint and return parsed JSON."""
    url = f"{PT_API}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_planetterp() -> list[dict]:
    """Fetch course + professor reviews, save raw JSON, return raw review dicts.

    Each returned dict is one raw review with its source attached. We save the
    untouched API response to documents/raw/ first, so the raw data is preserved
    in a consistent format before any cleaning happens.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_reviews: list[dict] = []

    targets = (
        [("course", c, f"course?name={c}") for c in COURSES]
        + [("professor", p, f"professor?name={p}") for p in PROFESSORS]
    )

    for kind, name, doc_url in targets:
        print(f"  fetching {kind}: {name} ...", end=" ", flush=True)
        try:
            data = fetch_json(kind, {"name": name, "reviews": "true"})
        except Exception as e:  # network hiccup, missing page, etc.
            print(f"FAILED ({type(e).__name__}: {e})")
            continue

        # Save the raw response untouched, before cleaning.
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        (RAW_DIR / f"{kind}_{slug}.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

        reviews = data.get("reviews") or []
        source_url = f"https://planetterp.com/{kind}/{slug}"
        for r in reviews:
            raw_reviews.append(
                {
                    "source": f"PlanetTerp — {kind} {name}",
                    "source_url": source_url,
                    "professor": r.get("professor") or "",
                    "course": r.get("course") or "",
                    "rating": r.get("rating"),
                    "expected_grade": r.get("expected_grade") or "",
                    "created": r.get("created") or "",
                    "review": r.get("review") or "",
                }
            )
        print(f"{len(reviews)} reviews")
        time.sleep(0.3)  # be polite to the API

    return raw_reviews


def load_manual_files() -> list[dict]:
    """Load any files the user saved into documents/ by hand.

    Supports .txt / .md (plain text) and .html (cleaned later). This is how
    Reddit or RateMyProfessors content can be added: the live sites block
    automated fetching, so paste/save the content here and it gets cleaned and
    chunked like everything else. The whole file is treated as one "review".
    """
    docs: list[dict] = []
    for path in sorted(MANUAL_DIR.glob("*")):
        if path.suffix.lower() not in {".txt", ".md", ".html", ".htm"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        docs.append(
            {
                "source": f"Manual file — {path.name}",
                "source_url": str(path),
                "professor": "",
                "course": "",
                "rating": None,
                "expected_grade": "",
                "created": "",
                "review": text,
            }
        )
    if docs:
        print(f"  loaded {len(docs)} manual file(s) from documents/")
    return docs


# =============================================================================
# 2. CLEAN
# =============================================================================
TAG_RE = re.compile(r"<[^>]+>")          # any HTML/XML tag
WS_RE = re.compile(r"[ \t]+")            # runs of spaces/tabs
BLANKLINES_RE = re.compile(r"\n{3,}")    # 3+ blank lines

# Boilerplate lines that appear on review pages but are not the review itself.
BOILERPLATE = re.compile(
    r"^\s*(read more|share|report|reply|edit|delete|helpful\??|"
    r"\d+ comments?|like|dislike|tags?:|all rights reserved|cookie|"
    r"sign in|log in|register|accept all)\b",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    """Turn raw text/HTML into clean, readable review text.

    Removes HTML tags, decodes HTML entities, normalizes line endings and
    whitespace, and drops common boilerplate lines.
    """
    if not text:
        return ""
    text = TAG_RE.sub(" ", text)          # strip HTML tags
    text = html.unescape(text)            # &amp; &nbsp; &#39; -> & (space) '
    text = text.replace(" ", " ")    # leftover non-breaking spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    kept = []
    for line in text.split("\n"):
        line = WS_RE.sub(" ", line).strip()
        if not line or BOILERPLATE.match(line):
            continue
        kept.append(line)
    cleaned = "\n".join(kept)
    cleaned = BLANKLINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def clean_reviews(raw_reviews: list[dict]) -> list[dict]:
    """Clean every review's text and drop empties / near-empties."""
    cleaned = []
    for r in raw_reviews:
        body = clean_text(r["review"])
        if len(body) < 15:   # skip blank or one-word reviews
            continue
        r = dict(r)
        r["review"] = body
        cleaned.append(r)
    return cleaned


def write_clean_documents(reviews: list[dict]) -> None:
    """Write one readable text file per source into data/clean/."""
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, list[dict]] = {}
    for r in reviews:
        by_source.setdefault(r["source"], []).append(r)

    for source, items in by_source.items():
        slug = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
        lines = [f"# {source}", f"# {len(items)} reviews", ""]
        for r in items:
            header = f"[Professor: {r['professor'] or 'n/a'} | Course: {r['course'] or 'n/a'}]"
            lines.append(header)
            lines.append(r["review"])
            lines.append("")
        (CLEAN_DIR / f"{slug}.txt").write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# 3. CHUNK
# =============================================================================
MIN_TAIL = 150  # never leave a trailing fragment smaller than this many chars


def split_long(text: str, size: int, overlap: int) -> list[str]:
    """Split text longer than `size` into overlapping windows (rare case).

    If the remaining text would leave a tiny tail (smaller than MIN_TAIL), it is
    folded into the current piece instead of becoming its own chunk. Otherwise a
    long review could produce a meaningless fragment like "esources." that has no
    standalone meaning and cannot be matched to any query.
    """
    if len(text) <= size:
        return [text]
    pieces, start, step = [], 0, size - overlap
    while start < len(text):
        # If a full-size window would leave a tiny tail, take the rest now.
        if len(text) - start <= size + MIN_TAIL:
            pieces.append(text[start:])
            break
        pieces.append(text[start : start + size])
        start += step
    return pieces


def chunk_reviews(reviews: list[dict]) -> list[dict]:
    """One review per chunk. Each chunk carries its professor/course context so
    an opinion is never separated from who it is about. Long reviews are split.
    """
    chunks: list[dict] = []
    for r in reviews:
        context = f"[Source: {r['source']} | Professor: {r['professor'] or 'n/a'} | Course: {r['course'] or 'n/a'}]"
        for piece in split_long(r["review"], CHUNK_SIZE, CHUNK_OVERLAP):
            text = f"{context}\n{piece}"
            chunks.append(
                {
                    "id": f"chunk-{len(chunks):04d}",
                    "text": text,
                    "source": r["source"],
                    "source_url": r["source_url"],
                    "professor": r["professor"],
                    "course": r["course"],
                    "rating": r["rating"],
                    "expected_grade": r["expected_grade"],
                    "created": r["created"],
                    "char_len": len(text),
                }
            )
    return chunks


def write_chunks(chunks: list[dict]) -> None:
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")


# =============================================================================
# main
# =============================================================================
def dedupe(reviews: list[dict]) -> list[dict]:
    """Course and professor pulls share the same reviews, so remove duplicates."""
    seen, unique = set(), []
    for r in reviews:
        key = (r["professor"], r["course"], r["review"][:200])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def main() -> None:
    print("1. LOAD")
    raw = load_planetterp() + load_manual_files()
    print(f"   -> {len(raw)} raw reviews collected\n")

    print("2. CLEAN")
    cleaned = clean_reviews(raw)
    cleaned = dedupe(cleaned)
    write_clean_documents(cleaned)
    print(f"   -> {len(cleaned)} clean, unique reviews "
          f"(written to {CLEAN_DIR.relative_to(ROOT)}/)\n")

    print("3. CHUNK")
    chunks = chunk_reviews(cleaned)
    write_chunks(chunks)
    print(f"   -> {len(chunks)} chunks (written to {CHUNKS_PATH.relative_to(ROOT)})\n")

    # 4. INSPECT — print one cleaned document and one chunk to read.
    print("4. INSPECT (read this to confirm cleaning worked)")
    sample_files = sorted(CLEAN_DIR.glob("*.txt"))
    if sample_files:
        print("=" * 70)
        print(f"ONE CLEANED DOCUMENT: {sample_files[0].name}")
        print("=" * 70)
        text = sample_files[0].read_text(encoding="utf-8")
        print(text[:1500] + ("\n... (truncated)" if len(text) > 1500 else ""))
    if chunks:
        print("\n" + "=" * 70)
        print("ONE CHUNK")
        print("=" * 70)
        print(chunks[0]["text"])


if __name__ == "__main__":
    main()
