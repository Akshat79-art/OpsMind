# OpsMind

A Retrieval-Augmented Generation (RAG) assistant for asking natural-language questions about Linux, networking, and DevOps fundamentals - and getting answers grounded in real reference documentation instead of guesswork.

## Overview

OpsMind builds a retrieval pipeline over a curated corpus of open documentation. Documents are parsed into a uniform record format, chunked, embedded, and stored in a vector database. Questions are answered by retrieving the most relevant chunks and passing them to an LLM with a grounded prompt, so responses stay anchored to source material.

The project is intentionally built in stages: from a minimal Q&A pipeline toward evaluation, re-ranking, multi-turn conversation, and containerized deployment. It's to showcase progression in both AI engineering fundamentals and DevOps practice.

## Status

Early development. Phase 1 (basic RAG pipeline) is in progress.

Completed so far:
- Corpus acquisition and a raw-data layout partitioned by topic.
- PDF extraction: raw PDFs are converted into per-page JSONL records.
- Markdown adapter (one record per heading).
- Cleaning pass (strip running headers/footers and page numbers, normalize ligatures, rejoin hyphenation).
- Chunking, embedding, and vector storage.

Planned next:
- Retrieval + grounded generation via the CLI.

## Pipeline

```
rawData/  ──▶  extractedData/  ──▶  processedData/  ──▶  chunks_data  ──▶ embeddings  ──▶  Chroma  ──▶  retrieval  ──▶  LLM answer
 (source)      (uniform records)     (cleaned text)    (text broken down)    (vectors)      (storage)       (top-k)          (cited)
```

Every stage writes to its own directory so any stage can be re-run without repeating the previous ones.

## Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.13 |
| Embeddings | `sentence-transformers` (`BAAI/bge-small-en-v1.5`) - Hosted Local |
| Chunking   | transformers (Autotokenizer)
| Vector store | Chroma |
| Generation | OpenRouter, free-tier model |
| PDF parsing | `pypdf` |
| Config | .env |
| Retrieval/generation | Hand-written pipeline (no framework) |

## Repository layout

```
OpsMind/
├── app/
│   ├── dataExtractionScripts/     # raw sources -> extractedData records
│   │   ├── pdfScripts.py
│   │   ├── mdScripts.py
│   │   └── ccnaScripts.py
│   ├── cleaning_scripts/          # extractedData -> processedData
│   │   ├── noise_detection.py
│   │   ├── textNormalization.py
│   │   ├── prose_length_filter.py
│   │   ├── pipeline.py
│   │   └── sourceRules/
│   │       ├── pdf_rules.py
│   │       └── md_rules.py
│   └── embedding_scripts/         # processedData -> chunks -> Chroma
│       ├── chunk.py
│       ├── embed.py
│       └── chroma_store.py
├── data/                          # not committed (see .gitignore)
│   ├── rawData/<category>/<slug>/
│   ├── extractedData/<category>/<slug>/records.jsonl
│   ├── processedData/<category>/<slug>/records.jsonl
│   ├── chunks_data/<category>/<slug>/chunks.jsonl
│   └── chroma/                    # persistent vector store
├── requirements.txt
└── README.md
```

## Getting started

### Prerequisites

- Python 3.13

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Usage

The scripts use paths relative to `app/dataExtractionScripts/`, so run them from that directory:

```powershell
cd app\dataExtractionScripts
python <fileName>.py
```

Output is written to `data/extractedData/<category>/<slug>/records.jsonl`.

## Roadmap

- **Phase 1** - Basic RAG pipeline: parse → chunk → embed → store → retrieve → grounded answer.
- **Phase 2** - Evaluation: labeled Q/A set; retrieval metrics (hit rate, recall@k, MRR) and answer faithfulness.
- **Phase 3** - Retrieval quality: hybrid keyword + vector search, cross-encoder re-ranking, query rewriting.
- **Phase 4** - Multi-turn conversation and memory.
- **Phase 5** - Agentic behavior (route between retrieval and direct answers).
- **Phase 6** - Productionize: Docker, CI/CD, monitoring, deployment.
- **Phase 7** - Scale corpus and infrastructure.

Subject to change.

## License

© 2026 Akshat Surana. All rights reserved.
