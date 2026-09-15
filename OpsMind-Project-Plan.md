# OpsMind — Project Plan

## Overview

**OpsMind** is a Retrieval-Augmented Generation (RAG) assistant that lets you ask natural-language questions about Linux, networking, and DevOps fundamentals and get accurate, source-grounded answers — instead of digging through scattered docs and wikis.

It's built on a curated corpus of open documentation (Arch Wiki, Kubernetes docs, Docker docs, and more), using an embedding-based retrieval pipeline paired with an LLM to generate grounded answers. The project is designed to grow in stages, mirroring a progression from AI engineering fundamentals into DevOps practice.

**Goals:**
- Build a working RAG system as a portfolio project, demonstrable on LinkedIn/GitHub.
- Use the project as a learning vehicle for both AI engineering and DevOps concepts.
- Expand it incrementally so each phase is its own visible milestone.

---

## Data Sources

| Topic area | Source | Access method |
|---|---|---|
| Linux fundamentals | Arch Wiki (via `tsgates/arch-wiki-markdown` GitHub mirror) | Download curated list of individual `.md` files via raw GitHub URLs (avoids full-repo clone) |
| Kubernetes | `kubernetes/website` GitHub repo | Shallow clone (`--depth 1`), filter `content/en/docs/` for `.md` files |
| Docker | `docker/docs` GitHub repo | Same clone-and-filter approach |
| Networking (stretch) | IETF RFCs via rfc-editor.org | Bulk download of plain-text RFCs (e.g. RFC 791, RFC 793) |
| General DevOps (stretch) | `kamranahmedse/developer-roadmap` | Clone and filter relevant topic files |

**Cleaning pipeline for all sources:**
1. Strip YAML frontmatter (`---` blocks).
2. Strip source-specific syntax (e.g. Hugo shortcodes `{{< ... >}}`).
3. Skip near-empty stub files.
4. Keep original file path/title as metadata for later citation.

---

## Tech Stack (starting point)

- **Chunking & embeddings:** `sentence-transformers` (or OpenAI/Cohere embeddings)
- **Vector store:** Chroma (local, simple) → Qdrant/pgvector later if scaling
- **Orchestration:** Raw retrieval + prompt logic first (for learning fundamentals); LangChain/LlamaIndex optional later
- **LLM:** Hosted API (Claude/OpenAI) or local via Ollama
- **UI:** Streamlit or Gradio for a zero-frontend demoable interface

---

## Phased Roadmap

**Phase 1 — Basic RAG pipeline**
Chunk the curated docs, embed with a simple model, store in Chroma, retrieve top-k chunks, pass to an LLM with a basic prompt. Goal: working end-to-end system, not optimization.

**Phase 2 — Improve retrieval quality**
Tune chunk size/overlap, try different embedding models, add hybrid search (keyword + vector) so exact technical terms aren't missed by pure semantic search.

**Phase 3 — Add evaluation**
Build a small test set of Q&A pairs. Measure retrieval precision and answer faithfulness instead of eyeballing results. (Strong signal of engineering maturity — good LinkedIn milestone.)

**Phase 4 — Re-ranking and query transformation**
Add a cross-encoder re-ranker to better sort retrieved chunks. Add query rewriting to clarify vague questions before retrieval.

**Phase 5 — Memory and multi-turn conversation**
Move from single-question Q&A to a chatbot that retains context across turns.

**Phase 6 — Agentic behavior**
Let the system decide when to retrieve vs. answer directly, or route between multiple tools/sources. Bridge into agent-based AI engineering.

**Phase 7 — Productionize and deploy**
Containerize with Docker, set up CI/CD (GitHub Actions), deploy to a free-tier host (Render/Fly.io/small VPS), add basic monitoring/logging. This is where DevOps skills plug in directly.

**Phase 8 — Scale data and infra**
Expand corpus (add networking RFCs, more DevOps tools), move to a more scalable vector DB if needed, consider caching/batching for cost and performance.

---

## LinkedIn / Demo Strategy

- Treat each phase as its own short post — builds a visible learning series rather than one big launch.
- Use a 30–60 second screen recording showing a real question getting a grounded, cited answer.
- Explain one technical decision per post (e.g. "chose hybrid search because pure vector search missed exact keyword matches").
- Link the GitHub repo with a clear README and (ideally) an architecture diagram.
- Keep the repo history itself as a visible trail — each phase as a branch or PR.

---

## Immediate Next Steps

1. Finalize the curated topic list for Linux fundamentals (Arch Wiki subset).
2. Run the collection scripts for Arch Wiki + Kubernetes docs.
3. Build the Phase 1 pipeline: chunk → embed → store → retrieve → generate.
4. Get a basic Streamlit UI running for the first demo.
5. Record and post the first LinkedIn demo.
