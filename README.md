# Terp-Tell_All

A retrieval-augmented question answering system over student reviews of
Computer Science professors at the University of Maryland (UMD).

---

## Domain

My system covers student reviews of Computer Science professors at the
University of Maryland. This knowledge is valuable because official sources do
not tell you what a class is actually like. The department website, the course
catalog, and the national ranking only tell you that a course exists and that
the program is highly ranked. They do not tell you which professors explain
concepts clearly, how hard the exams are, or whether a section is worth taking.

That information is hard to find because it is scattered across informal places
like PlanetTerp, RateMyProfessors, and Reddit. It is opinion-heavy and
inconsistent, and there is no single place to get a straight answer. My system
pulls these reviews together so a student can ask one question and get an answer
based on what many students actually said.

---

## Document Sources

All review text comes from the PlanetTerp public API. PlanetTerp is a UMD-specific site where students rate and review courses and professors. I pull both course pages (reviews from every professor of that course) and professor
pages (one professor's reviews across all their courses), then remove duplicates. I planned to also use Reddit and RateMyProfessors, but both sites block automated collection, so the final corpus is PlanetTerp only.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | PlanetTerp — CMSC131 | Review site (course) | https://planetterp.com/course/CMSC131/reviews |
| 2 | PlanetTerp — CMSC132 | Review site (course) | https://planetterp.com/course/CMSC132/reviews |
| 3 | PlanetTerp — CMSC216 | Review site (course) | https://planetterp.com/course/CMSC216/reviews |
| 4 | PlanetTerp — CMSC250 | Review site (course) | https://planetterp.com/course/CMSC250/reviews |
| 5 | PlanetTerp — CMSC330 | Review site (course) | https://planetterp.com/course/CMSC330/reviews |
| 6 | PlanetTerp — CMSC351 | Review site (course) | https://planetterp.com/course/CMSC351/reviews |
| 7 | PlanetTerp — Nelson Padua-Perez | Review site (professor) | https://planetterp.com/professor/padua-perez |
| 8 | PlanetTerp — Clyde Kruskal | Review site (professor) | https://planetterp.com/professor/kruskal |
| 9 | PlanetTerp — Anwar Mamat | Review site (professor) | https://planetterp.com/professor/mamat |
| 10 | PlanetTerp API | API endpoint (data source) | https://planetterp.com/api/v1 |

---

## Chunking Strategy

My documents are made up of many short, separate student reviews. Each review is one person's opinion about one professor or course, and it is usually only a few sentences long. Because of this, I split on review boundaries and put one
review in each chunk. This keeps each opinion whole, so a search can return a clear point of view instead of a confusing blob.

**Chunk size:** One review per chunk. If a review is longer than 800 characters (about 150 tokens), it is split into smaller pieces of that size.

**Overlap:** 0 characters for normal splitting, because each chunk is already a complete review. A small 50-character overlap is only used when a long review has to be split into pieces.

**Why these choices fit your documents:** If chunks were too big, one chunk
would mix reviews about different professors. If chunks were too small, one
review would get cut in half and lose its meaning. One review per chunk avoids
both problems. Before chunking, I clean each review: I strip HTML tags, decode
HTML entities like `&amp;` and `&nbsp;`, normalize line endings and whitespace,
and drop short or empty reviews. Each chunk also keeps a header with its source,
professor, and course, so an opinion is never separated from who it is about.

**Final chunk count:** 3,622 chunks (from 3,027 raw reviews, reduced to 2,669
clean unique reviews after cleaning and de-duplication).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` from the sentence-transformers library. I
chose it because it runs locally with no API key and no rate limits, it is fast,
and it works well on short pieces of text like student reviews. The chunks are
stored in a ChromaDB vector store that uses cosine distance.

**Production tradeoff reflection:** If I were deploying this for real users and
cost was not a constraint, I would consider a larger embedding model, such as a
hosted OpenAI embedding model or a bigger sentence-transformers model. A larger
model would understand the meaning of the reviews more accurately, so the search
would return reviews that match the question better. The tradeoffs I would weigh
are accuracy on my kind of text (a bigger model usually understands slang and
casual review language better), context length (how much text the model can read
at once, which matters less for me because my reviews are short), latency (bigger
models are slower), and local versus API-hosted (an API model adds cost and a
network dependency but removes the need to run the model myself). For this
project the small local model was the right choice because my reviews are short
and I wanted it to be fast and free.

---

## Grounded Generation

My system stops the model from answering beyond the retrieved reviews in two
ways: the system prompt and the way I format the context.

**System prompt grounding instruction:** I tell the model to use only the
provided reviews and to refuse when they are not enough. The exact instruction
is:

> "Answer the question using ONLY the information in the provided reviews below.
> Do not use outside knowledge. If the reviews do not contain enough information
> to answer, reply exactly: 'I don't have enough information on that.' When you
> state a fact, cite the review it came from using its number, like (Source 1)."

I also set the model's temperature to 0.2 so it stays close to the review text
and does not hallucinate.

**How source attribution is surfaced in the response:** Attribution is handled
two ways so it is always present. First, each retrieved review is numbered in
the context (Source 1, Source 2, ...), and the model is told to cite those
numbers in its answer. Second, after the model answers, my code appends the real
source documents (the PlanetTerp page names and URLs) below the answer. So even
if the model forgets to cite, the user still sees which documents the answer came
from.

---

## Evaluation Report

I ran all 5 questions from `planning.md` through the live system.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about the difficulty of Nelson Padua-Perez's exams in CMSC131 and CMSC132? | His exams are hard and intentionally so; some scores in the low 60s. | Said there were no CMSC132 reviews for him, then gave mixed CMSC131 opinions: first midterm easy, second "ridiculously difficult." | Partially relevant | Partially accurate |
| 2 | Which professor do students recommend for CMSC330? | Anwar Mamat is commonly recommended. | Recommended Mamat and Michael Hicks (both real CMSC330 professors) with reasons, but also listed Kauffman, who mostly teaches CMSC216. | Partially relevant | Partially accurate |
| 3 | What do students think of Clyde Kruskal for CMSC351? | Mixed to positive: knowledgeable but the class and exams are hard. | Gave a nuanced, well-cited mix: passionate algorithms expert and worth taking, but lectures can be disorganized and the class is hard. | Relevant | Accurate |
| 4 | Do students consider CMSC216 a hard course, and why? | Yes, mainly because of the heavy workload and low-level C/systems content. | Said yes, it is hard, but supported it with some reviews from other courses (CMSC351, CMSC250) mixed in with the real CMSC216 reviews. | Partially relevant | Partially accurate |
| 5 | Do students on PlanetTerp and RateMyProfessors agree about Nelson Padua-Perez? | Both platforms show a similar split. | "I don't have enough information on that." | Off-target | Inaccurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

Overall, the system did well on questions about a single professor or course
(Q3 especially). It was weaker when a question named one specific course,
because reviews about other hard courses look similar and crowded into the
results.

---

## Failure Case Analysis

**Question that failed:** Q5 — "Do students on PlanetTerp and RateMyProfessors
agree in their opinion of Nelson Padua-Perez?"

**What the system returned:** "I don't have enough information on that."

**Root cause (tied to a specific pipeline stage):** This failed at the document
ingestion stage, not at retrieval or generation. My corpus only contains
PlanetTerp reviews. I had planned to also collect RateMyProfessors and Reddit
data, but RateMyProfessors loads its reviews with JavaScript through a private
API, and Reddit blocks automated requests (it returned HTTP 403). So neither
source was ever ingested. Because the question asks the system to compare two
platforms and one of those platforms is missing from the data, the system
correctly followed its grounding rule and refused to answer. The refusal is the
right behavior, but the question can never be answered with the data I have.

**What you would change to fix it:** I would fix this at the ingestion stage by
collecting the missing platform properly. For Reddit I would use the official
Reddit API with an authenticated key instead of plain web requests. For
RateMyProfessors I would call its internal GraphQL endpoint or save the rendered
pages by hand and load them through the manual-file path my ingestion script
already supports. Once those reviews are in the corpus and tagged with their
platform, the system would have content from both sites and could actually
compare them.

A second, smaller failure pattern showed up in Q4. When a question named a
specific course (CMSC216), retrieval pulled in reviews about other hard courses
(CMSC351, CMSC250) because they are semantically similar on the idea of "this
course is hard." The embedding model does not weigh the exact course code
("CMSC216") strongly enough. I would fix this by passing the course code as a
metadata filter to ChromaDB, so retrieval is limited to that course before
ranking by similarity.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the Chunking
Strategy in `planning.md` before any code gave me exact numbers to build toward.
Because I had already decided "one review per chunk, 800-character limit,
50-character overlap," I could tell the AI tool exactly what to implement, and I
could check the output against a clear target instead of guessing. It also made
the rest of the pipeline simpler: since each chunk is one whole review, my
choice of top-k = 5 directly means "five student opinions," which made the
retrieval and generation steps easy to reason about.

**One way your implementation diverged from the spec, and why:** My spec said to
split any review longer than 800 characters into 800-character pieces. When I
actually inspected the chunks, I found that this rule sometimes left a tiny
leftover piece at the end of a long review, like "esources." or "M!!!". Those
fragments have no standalone meaning and cannot match any query. So I changed the
implementation: if splitting would leave a piece smaller than 150 characters, I
fold that leftover into the previous piece instead of making it its own chunk.
This kept every chunk meaningful and dropped the total chunk count from 3,880 to
3,622. The spec gave the target, but inspecting real output showed an edge case
the spec did not anticipate.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* My Documents table and Chunking Strategy section from
  `planning.md`, and the instruction to write the ingestion and chunking script
  with one review per chunk, an 800-character limit, and 50-character overlap.
- *What it produced:* A standard-library Python script (`ingest.py`) that fetches
  reviews from the PlanetTerp API, saves the raw JSON, cleans the text (strips
  HTML, decodes entities, normalizes whitespace), and chunks one review per
  chunk. It printed one cleaned document and one chunk so I could inspect them.
- *What I changed or overrode:* After printing five chunks, I found tiny
  fragments left over from splitting long reviews. I directed the AI to change
  the split logic so that a leftover piece smaller than 150 characters is folded
  into the previous chunk. This removed the meaningless fragments.

**Instance 2**

- *What I gave the AI:* My Retrieval Approach section and the plan to embed
  chunks with all-MiniLM-L6-v2, store them in ChromaDB, retrieve the top 5, and
  generate a grounded, cited answer.
- *What it produced:* `retrieval.py` (embedding, ChromaDB storage with metadata,
  and a `retrieve()` function) and `app.py` (a Groq prompt with grounding rules
  and source attribution), plus a Gradio web interface in `web.py`.
- *What I changed or overrode:* My original plan said to generate answers with
  the Claude API, but the project's `requirements.txt` uses Groq, so I overrode
  that and used Groq's `llama-3.3-70b-versatile`. I also tested retrieval first,
  saw that course-specific questions pulled in other courses, and noted a
  metadata filter as the fix instead of accepting the default behavior.
