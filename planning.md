# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

My domain is student reviews of Computer Science professors at the University of Maryland (UMD).UMD's CS program is ranked among the top 10 in the country, but I feel that ranking is driven largely by the school's strong industry connections and the volume of internships students land at major tech companies — not necessarily by how effectively individual professors teach. That gap is exactly what makes this domain valuable: official sources (the department website, course catalogs, the program's national ranking) tell you nothing about what it's actually like to take a class with a given professor.

The information students really want, which professors explain concepts clearly, how hard the exams are, whether a section is worth taking, lives in scattered places such as PlanetTerp reviews, RateMyProfessors ratings, and Reddit threads on r/UMD. It's opinion-heavy, inconsistent, and spread across multiple platforms, so there's no single place to get a straight answer. A retrieval system that pulls these reviews together to answer specific questions about UMD CS professors fills the gap.

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit (r/UMD) | Open discussion thread on overall quality of UMD professors; candid, conversational perspective | https://www.reddit.com/r/UMD/comments/lnvc65/quality_of_professors/ |
| 2 | PlanetTerp — CMSC131 | Student reviews + grade data for intro programming (course-level subtopic) | https://planetterp.com/course/CMSC131/reviews |
| 3 | PlanetTerp — CMSC132 | Reviews for Object-Oriented Programming II; section-by-section comparisons | https://planetterp.com/course/CMSC132/reviews |
| 4 | PlanetTerp — CMSC216 | Reviews for Intro to Computer Systems | https://planetterp.com/course/CMSC216/reviews |
| 5 | PlanetTerp — CMSC250 | Reviews for Discrete Structures | https://planetterp.com/course/CMSC250/reviews |
| 6 | PlanetTerp — CMSC330 | Reviews for Organization of Programming Languages | https://planetterp.com/course/CMSC330/reviews |
| 7 | PlanetTerp — CMSC351 | Reviews for Algorithms | https://planetterp.com/course/CMSC351/reviews |
| 8 | PlanetTerp — Nelson Padua-Perez | Per-professor review page; many reviews across his courses | https://planetterp.com/professor/padua-perez |
| 9 | PlanetTerp — Clyde Kruskal | Per-professor review page (algorithms) | https://planetterp.com/professor/kruskal |
| 10 | PlanetTerp — Anwar Mamat | Per-professor review page (CMSC330) | https://planetterp.com/professor/mamat |
| 11 | RateMyProfessors — UMD CS faculty search | Different platform/perspective; ratings + tags + free-text reviews | https://www.ratemyprofessors.com/search/professors/1270?q=*&did=11 |
| 12 | RateMyProfessors — Nelson Padua-Perez | Same professor as #8 on a different platform — lets you compare perspectives/agreement | https://www.ratemyprofessors.com/professor/268534 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
