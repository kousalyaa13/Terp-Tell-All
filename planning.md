# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

My domain is student reviews of Computer Science professors at the University of Maryland (UMD). UMD's CS program is ranked among the top 10 in the country, but I feel that ranking is driven largely by the school's strong industry connections and the volume of internships students land at major tech companies — not necessarily by how effectively individual professors teach. That gap is exactly what makes this domain valuable: official sources (the department website, course catalogs, the program's national ranking) tell you nothing about what it's actually like to take a class with a given professor.

The information students really want, which professors explain concepts clearly, how hard the exams are, whether a section is worth taking, lives in scattered places such as PlanetTerp reviews, RateMyProfessors ratings, and Reddit threads on r/UMD. It's opinion-heavy, inconsistent, and spread across multiple platforms, so there's no single place to get a straight answer. A retrieval system that pulls these reviews together to answer specific questions about UMD CS professors fills the gap.

---

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

**Chunk size:** The chunk size would be one student review per chunk. Each review is its own complete thought, so I split on review boundaries instead of cutting by length. If a single review is longer than about 800 characters (roughly 150 tokens), I will cut it into smaller pieces of that size.

**Overlap:** The overlap would be 0 characters for normal splitting, because each chunk is already a complete review. I only use a small 50-character overlap in the rare case where one very long review has to be cut by the 800-character limit.

**Reasoning:** My documents are made up of many short and separate student reviews. Each review is one person's opinion about one professor or course. Each review is usually only a few sentences long. Because of this, I want each chunk to hold one complete review. Splitting by meaning keeps each opinion whole, so the search step can return a clear point of view instead of a confusing blob. If my chunks were too big, one chunk would mix together reviews about different professors. If my chunks were too small, one review would get cut in half and lose its meaning. I don't need overlap for normal splitting because the review boundaries already give me complete chunks.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** I will use the all-MiniLM-L6-v2 model from the sentence-transformers library. It works well for short pieces of text like student reviews, which is exactly the kind of data I have.

**Top-k:** I will retrieve the top 5 chunks for each query. Since each chunk is one student review, this gives me 5 different opinions to answer from. One review is not enough, because a single opinion can be biased. Five reviews let me find what students agree on, while still keeping the results focused and not too noisy.

**Production tradeoff reflection:** If I were building this for real users and cost was not a problem, I would think about using a larger embedding model, such as one of OpenAI's embedding models or a bigger sentence-transformers model. A larger model would understand the meaning of the reviews more accurately, so the search step would return reviews that match the question better. The tradeoffs I would weigh are: accuracy on my kind of text (a bigger model usually understands slang and casual review language better), context length (how much text the model can read at once, which matters less for me because my reviews are short), and latency and cost (bigger models are slower and cost money per request). For this project, I chose the small model because my reviews are short and I want it to be fast and free. For a real product, I would likely trade some speed and money for the better accuracy of a larger model.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about the difficulty of Nelson Padua-Perez's exams in CMSC131 and CMSC132? | Students say his exams are harder than other sections and that he makes them difficult on purpose. Some reviews mention exam scores in the low 60s. |
| 2 | Which professor do students recommend for CMSC330 (Organization of Programming Languages)? | Students point to Anwar Mamat as a commonly recommended professor for CMSC330. |
| 3 | What do students think of Clyde Kruskal as a professor for CMSC351 (Algorithms)? | Reviews give a mixed-to-positive view: students find him knowledgeable but say the course and his exams are challenging. |
| 4 | Do students consider CMSC216 (Intro to Computer Systems) a hard course, and why? | Students generally call it difficult, mainly because of the heavy workload and the jump to lower-level C and systems programming. |
| 5 | Do students on PlanetTerp and RateMyProfessors agree in their opinion of Nelson Padua-Perez? | Both platforms show a similar split: students respect his teaching but find his class and exams very hard, so the two sources mostly agree. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Conflicting and biased reviews.** Student reviews often disagree. One student may love a professor while another hates the same professor. Many reviews are also written by angry students right after a bad grade, so they are extreme and one-sided. This means my system might give an answer based on one biased review instead of the overall opinion. To reduce this, I retrieve the top 5 chunks so the answer is based on several reviews, not just one.

2. **Reviews that do not name the professor or course.** Some reviews say "this class was hard" without saying which professor or course they mean, especially on Reddit. When this context is missing from a chunk, the system can attach an opinion to the wrong professor or course. This is a risk because my chunks are split per review, so a chunk may not carry the professor's name with it. To reduce this, I will attach the source and professor or course name to each chunk as metadata during ingestion.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

![Mermaid JS Diagram](images\mermaid-diagram-2026-06-07-192352.png)

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

**Milestone 3 — Ingestion and chunking:** I will use Claude to write the ingestion and chunking code. As input, I will give Claude my Documents table and my Chunking Strategy section. I will ask it to write a script that loads the saved review text and a `chunk_text()` function that splits the text into one review per chunk, with an 800-character limit and 50-character overlap as a backup. I expect it to produce clean Python functions plus example output. I will verify the output by printing a few chunks and checking that each chunk holds one complete review and that no review is cut in the middle.

**Milestone 4 — Embedding and retrieval:** I will use Claude to write the embedding and retrieval code. As input, I will give it my Retrieval Approach section. I will ask it to embed each chunk with all-MiniLM-L6-v2, store the vectors in ChromaDB, and write a function that takes a question and returns the top 5 most similar chunks. I expect working Python code for embedding, storing, and searching. I will verify it by running my 5 evaluation questions and checking that the chunks it returns are actually about the right professor or course.

**Milestone 5 — Generation and interface:** I will use Claude to write the generation step and a simple interface. As input, I will give it my Evaluation Plan and my retrieval function. I will ask it to send the user's question plus the top 5 retrieved reviews to the Groq API (the LLM library listed in requirements.txt) and return an answer that cites which reviews it used. I expect a small command-line (or simple web) interface where I type a question and get a cited answer. I will verify it by asking my 5 evaluation questions and comparing the answers to my expected answers.
