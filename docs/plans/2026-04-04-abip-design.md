# Agentic Book Intelligence Platform (ABIP) — Design Document

**Date:** 2026-04-04
**Status:** Approved
**Author:** Trevor Campbell

---

## 1. Platform Overview & Goals

### What It Is

A multi-agent AI system that provides a personal book intelligence assistant. Users can chat naturally about books, track their reading, get recommendations, and receive AI-synthesized insights. The platform is simultaneously a genuine personal reading tool and a portfolio-quality reference architecture demonstrating every domain of the Claude Certified Architect: Foundations certification.

### Primary Goals

1. Cover all 5 cert domains with working, non-trivial implementations
2. Be a genuinely useful personal reading tool (chat, tracking, research)
3. Serve as a portfolio-quality reference architecture for agentic systems on Databricks

### What a User Can Do

- **Chat with AI:** "What should I read after Dune?" / "Summarize what I know about Brandon Sanderson's writing style"
- **Ask data questions:** "How many books did I finish in Q1?" / "What genres am I reading most?"
- **Trigger research:** "Find me everything about the Mistborn series — ratings, reviews, related books"
- **View dashboards:** Reading stats, genre breakdown, reading velocity, AI-generated reading briefs

### Out of Scope (Phase 1)

- Social/sharing features
- Mobile app
- Multi-user support

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABRICKS APP (Streamlit)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  AI Chat UI  │  │  Dashboards  │  │  Reading List Manager  │  │
│  └──────┬──────┘  └──────────────┘  └───────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │ user messages
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              COORDINATOR AGENT (Claude claude-sonnet-4-6)              │
│   - Receives user requests                                       │
│   - Decomposes tasks, routes to subagents                        │
│   - Aggregates results, generates final response                 │
│   - Manages hooks (PostToolUse, PreToolUse)                      │
└────────┬────────────────┬────────────────┬───────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ BOOK DISCOVERY│  │    DATA      │  │  SYNTHESIS / CHAT    │
│    AGENT     │  │INTELLIGENCE  │  │       AGENT          │
│              │  │    AGENT     │  │                      │
│ - Search     │  │ - Query      │  │ - NL answers         │
│   books      │  │   Delta      │  │ - Reading reports    │
│ - Fetch      │  │   tables     │  │ - Recommendations    │
│   metadata   │  │ - Reading    │  │ - Cross-agent        │
│ - Get ratings│  │   stats      │  │   synthesis          │
│ - Find       │  │ - Trigger    │  │                      │
│   editions   │  │   jobs       │  │                      │
│ - Reviews    │  │              │  │                      │
└──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘
       │                 │                      │
       ▼                 ▼                      ▼
┌─────────────┐  ┌───────────────┐  ┌──────────────────────┐
│  MCP SERVER │  │  MCP SERVER   │  │     MCP SERVER       │
│  #1: Books  │  │ #2: Databricks│  │  #3: Annotations     │
│             │  │               │  │                      │
│ Hardcover + │  │ Delta tables  │  │ Personal notes,      │
│ Open Library│  │ Unity Catalog │  │ highlights, tags,    │
│ APIs        │  │ Job triggers  │  │ reading journal      │
└─────────────┘  └───────┬───────┘  └──────────────────────┘
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
   ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
   │ DELTA LAKE  │ │  DATABRICKS  │ │   DATABRICKS    │
   │   TABLES    │ │  FM / VECTOR │ │   WORKFLOWS     │
   │             │ │   SEARCH     │ │                 │
   │ books       │ │              │ │ Nightly API sync│
   │ reading_log │ │ Embeddings   │ │ Weekly digest   │
   │ authors     │ │ Semantic     │ │ job             │
   │ annotations │ │ book search  │ │                 │
   │ enrichment  │ │              │ │                 │
   └─────────────┘ └──────────────┘ └─────────────────┘
```

### Key Architectural Decisions

- **Claude SDK Agent framework** manages coordinator + subagent lifecycle, hooks, and context passing
- **MCP servers run as separate processes**, registered in `.mcp.json` — project-scoped and version-controlled
- **Databricks App** calls the coordinator agent via the Claude API — the app itself is stateless
- **Subagents have scoped tool access** — each subagent only gets the tools for its MCP server (cert Domain 2.3)
- **All subagent communication routes through the coordinator** — no direct subagent-to-subagent calls (cert Domain 1.2)

---

## 3. MCP Servers

All three servers registered in project-scoped `.mcp.json` with environment variable credential expansion. No secrets committed to version control.

### MCP Server #1 — Books API Server

Wraps Hardcover API (primary) + Open Library API (fallback) + Google Books API (review supplemental).

| Tool | Description |
|------|-------------|
| `search_books` | Search by title, author, ISBN, genre |
| `get_book_details` | Full metadata: description, ratings, pages, genres, cover |
| `get_book_editions` | All editions of a work (formats, languages, publishers) |
| `get_author_details` | Author bio, bibliography, similar authors |
| `get_recommendations` | Books similar to a given title |
| `get_trending_books` | Trending/popular by genre or overall |
| `get_book_reviews` | Fetch all reviews for a specific book (title/ISBN) |
| `search_reviews` | Full-text search across reviews by keyword, sentiment, or topic |

All tools return structured error responses with `errorCategory`, `isRetryable`, and human-readable descriptions.

### MCP Server #2 — Databricks Server

Wraps Databricks SQL Warehouse + REST API. Exposes Delta tables and job management as tools. Exposes MCP Resources for the Delta schema catalog.

| Tool | Description |
|------|-------------|
| `query_reading_log` | Query personal reading history with filters |
| `get_reading_stats` | Aggregated stats: books/month, avg rating, genre breakdown |
| `search_my_library` | Vector search across personal library using FM embeddings |
| `add_book_to_library` | Add a book to the reading log with status |
| `update_reading_status` | Update read/reading/want-to-read status + rating |
| `trigger_enrichment_job` | Trigger Databricks Workflow to enrich a book record |
| `get_job_status` | Check status of a running enrichment job |

### MCP Server #3 — Annotations Server

Lightweight local server managing personal notes, highlights, and reading journal entries. Stored in SQLite.

| Tool | Description |
|------|-------------|
| `add_annotation` | Save a note, highlight, or quote from a book |
| `get_annotations` | Retrieve annotations for a book or date range |
| `search_annotations` | Full-text search across all annotations |
| `add_journal_entry` | Log a reading session with thoughts/mood |
| `get_journal_entries` | Retrieve journal entries by book or date |

---

## 4. Multi-Agent System

### Coordinator Agent

**Model:** `claude-sonnet-4-6`

**Responsibilities:**
- Analyze incoming request and determine which subagents to invoke
- Spawn subagents in parallel when tasks are independent (cert Domain 1.3)
- Pass explicit, complete context to each subagent — no implicit context inheritance
- Aggregate and synthesize subagent results
- Manage escalation when a subagent fails (cert Domain 1.4)
- Run `PreToolUse` and `PostToolUse` hooks

**Example routing logic:**
- "What should I read next?" → Book Discovery + Data Intelligence in parallel, then Synthesis
- "How many books did I read this year?" → Data Intelligence only
- "Find reviews of Project Hail Mary" → Book Discovery only
- "Write me a reading brief on Dune" → all three agents, then Synthesis

### Subagent Definitions

**Book Discovery Agent**
- Allowed tools: MCP Server #1 only
- Specialized for book research and citation formatting
- Returns structured findings with source attribution

**Data Intelligence Agent**
- Allowed tools: MCP Server #2 only
- Specialized for data queries, statistical summaries, and Delta table operations
- Returns structured data results with schema context

**Synthesis / Chat Agent**
- Allowed tools: MCP Server #3 + `verify_fact` cross-role tool
- Specialized for NL generation, recommendation narrative, and report writing
- Returns final user-facing prose, reports, or recommendations

### Hooks (cert Domain 1.5)

| Hook | Type | Purpose |
|------|------|---------|
| Normalize API timestamps | `PostToolUse` | Converts Unix timestamps (Hardcover) and ISO 8601 (Open Library) to consistent format |
| Enforce read-only mode | `PreToolUse` | Blocks write operations when session is in read-only mode |
| Audit logging | `PostToolUse` | Writes every tool call + result to `intelligence.audit_log` Delta table |

### Agentic Loop (cert Domain 1.1)

- Continue when `stop_reason == "tool_use"` — execute tool, append result, send next request
- Terminate when `stop_reason == "end_turn"` — return final response to UI
- No arbitrary iteration caps as the primary stopping mechanism

---

## 5. Databricks Backend

### Unity Catalog Structure

```
catalog: abip
└── schema: books
    ├── books              (master book catalog)
    ├── authors            (author profiles)
    ├── editions           (edition-level detail)
    ├── reviews            (synced review data)
    └── enrichment_queue   (books pending AI enrichment)
└── schema: reading
    ├── reading_log        (personal read/reading/want-to-read)
    ├── reading_sessions   (session-level journal entries)
    └── annotations        (highlights, notes, quotes)
└── schema: intelligence
    ├── book_embeddings    (Databricks FM vector embeddings)
    ├── reading_briefs     (AI-generated summaries per book)
    └── audit_log          (all agent tool calls + results)
```

### Databricks FM / Vector Search

- **Embeddings model:** `databricks-gte-large-en` for book descriptions, reviews, and annotations
- **Vector Search index** on `book_embeddings` — powers `search_my_library` for semantic queries
- **Foundation Model API** used by Synthesis Agent for lightweight summarization (offloads token volume from Claude)

### Databricks Workflows

**Job 1: Nightly Book Sync**
- Schedule: nightly 2am
- Calls Hardcover API → upserts into `books.books` and `books.reviews`
- On completion: triggers enrichment job for new books

**Job 2: Book Enrichment Pipeline**
- Triggered by: Job 1 completion or `trigger_enrichment_job` MCP tool call
- Generates FM embeddings → stores in `intelligence.book_embeddings`
- Generates AI reading brief via Claude API → stores in `intelligence.reading_briefs`

**Job 3: Weekly Reading Digest**
- Schedule: Sunday 8am
- Queries `reading.reading_log` for the week
- Calls Claude API to generate personalized weekly reading digest
- Stores result for display in the Databricks App

### Claude Code Configuration (cert Domain 3)

- **`CLAUDE.md`** at project root with project context, coding standards, and Databricks conventions
- **`.claude/rules/`** with path-scoped rule files:
  - `databricks.md` — active for `**/*.py` files
  - `mcp-servers.md` — active for `mcp_servers/**/*`
- **`.claude/commands/`** with custom slash commands: `/sync-books`, `/run-enrichment`, `/generate-digest`
- **`.mcp.json`** at project root registering all 3 MCP servers with env var credential expansion

---

## 6. Databricks App (UI)

Built as a **Streamlit app** deployed on Databricks Apps.

### Pages

| Page | Description |
|------|-------------|
| **Chat** | Conversational interface to the Coordinator Agent. Streams responses. Shows tool call activity in collapsible sidebar. |
| **My Library** | Table view of `reading.reading_log`. Add/update books inline. Click a book to view AI-generated reading brief. |
| **Discover** | Book search + semantic search bar + recommendation browser + review browser. |
| **Insights Dashboard** | Reading stats, velocity trend, genre breakdown, avg rating charts. Latest weekly digest. |
| **Annotations** | Browse, search, and add personal notes, highlights, and journal entries. |

### App Architecture Notes

- App is stateless — all data lives in Delta tables or MCP Server #3
- Claude API calls made server-side — API key stored as Databricks secret
- Databricks SDK used directly for read-only dashboard queries (MCP Server #2 reserved for agent-driven operations)

---

## 7. Certification Coverage Map

### Domain 1: Agentic Architecture & Orchestration (27%)

| Task Statement | Implementation |
|----------------|----------------|
| 1.1 Agentic loops | Coordinator's `stop_reason` loop — `tool_use` continues, `end_turn` terminates |
| 1.2 Multi-agent coordinator-subagent | Coordinator → 3 subagents, all comms route through coordinator |
| 1.3 Subagent invocation & context passing | Parallel `Task` tool calls; full findings passed explicitly in each subagent prompt |
| 1.4 Multi-step workflows & handoff | Enrichment pipeline gates; structured handoff format for failed enrichments |
| 1.5 Agent SDK hooks | `PostToolUse` normalization; `PreToolUse` enforcement; audit logging |
| 1.6 Task decomposition | Prompt chaining for predictable queries; dynamic decomposition for open-ended research |
| 1.7 Session state & forking | Named sessions for long research tasks; `fork_session` for parallel recommendation strategies |

### Domain 2: Tool Design & MCP Integration (18%)

| Task Statement | Implementation |
|----------------|----------------|
| 2.1 Tool interface design | All MCP tools have descriptions with input formats, examples, edge cases, clear differentiation |
| 2.2 Structured error responses | All MCP tools return `errorCategory`, `isRetryable`, human-readable message |
| 2.3 Tool distribution across agents | Each subagent has scoped tool access; Synthesis Agent gets `verify_fact` as limited cross-role tool |
| 2.4 MCP server integration | Project-scoped `.mcp.json`; env var credential expansion; MCP Resources expose Delta schema |
| 2.5 Built-in tools | Claude Code used throughout development per best practices |

### Domain 3: Claude Code Configuration & Workflows (20%)

| Task Statement | Implementation |
|----------------|----------------|
| 3.1 CLAUDE.md hierarchy | Root `CLAUDE.md` + `.claude/rules/` directory with topic-scoped files |
| 3.2 Custom slash commands & skills | `/sync-books`, `/run-enrichment`, `/generate-digest`; skills with `context: fork` |
| 3.3 Path-specific rules | `databricks.md` scoped to `*.py`; `mcp-servers.md` scoped to `mcp_servers/**/*` |
| 3.4 Plan mode vs direct execution | Used throughout development per complexity |
| 3.5 Iterative refinement | TDD for MCP tools; few-shot examples for extraction prompts |
| 3.6 CI/CD integration | GitHub Actions with Claude Code `-p` flag for automated PR review + test generation |

### Domain 4: Prompt Engineering & Structured Output (20%)

| Task Statement | Implementation |
|----------------|----------------|
| 4.1 Explicit criteria prompts | Review analysis prompts with specific criteria for meaningful insights vs noise |
| 4.2 Few-shot prompting | Synthesis Agent uses 2-4 few-shot examples for recommendation narrative and reading briefs |
| 4.3 Structured output via tool use | JSON schemas for all MCP responses; `tool_choice: "any"` for unknown document types |
| 4.4 Validation & retry loops | Enrichment pipeline retries with appended validation errors on schema failures |
| 4.5 Batch processing | Weekly digest job uses Message Batches API for cost-efficient bulk enrichment |

### Domain 5: Context Management & Reliability (15%)

| Task Statement | Implementation |
|----------------|----------------|
| Context window management | Coordinator passes structured summaries (not full transcripts) to subagents; Explore subagent for verbose discovery |
| Reliability & error handling | Subagents handle transient errors locally; propagate only unrecoverable failures with partial results |
| Human-in-the-loop | Enrichment pipeline flags low-confidence extractions for manual review before writing to Delta |

---

## 8. Phase 2 Addendum — Event-Driven Agent Orchestration

Phase 2 is purely additive. No Phase 1 components are replaced. Databricks Workflows are promoted from "data sync" to "agent orchestration backbone."

### What Changes

Workflows move from scheduled jobs that call APIs to event-driven DAGs where task completions, file arrivals, and Delta table changes trigger agent pipelines automatically.

### New / Upgraded Jobs

**Job 1 (upgraded): Intelligent Nightly Sync**
- After syncing new books, Coordinator Agent runs automatically to classify books, detect series relationships, and cross-reference with reading history

**Job 4 (new): Delta Live Tables Enrichment Pipeline**
- DLT pipeline monitors `books.enrichment_queue`
- On new record: triggers Book Discovery Agent → Synthesis Agent → writes to `intelligence.reading_briefs`
- Fully autonomous background enrichment

**Job 5 (new): Continuous Annotation Intelligence**
- Triggered by new entries in `reading.annotations`
- Runs Synthesis Agent to detect themes, update affinity scores, surface connections to other books
- Powers increasingly personalized recommendations over time

### New Component: Webhook Receiver

Lightweight FastAPI endpoint deployed as a Databricks App:
- Receives webhooks from Hardcover or a self-polling service
- Writes to `books.enrichment_queue`
- Triggers the DLT pipeline

### Phase 2 Cert Coverage Additions

| Domain | What Phase 2 Adds |
|--------|-------------------|
| Domain 1.4 | Programmatic workflow gates — enrichment agent blocked until sync confirms data integrity |
| Domain 1.6 | Dynamic decomposition driven by Workflow metadata (number of new books determines parallelism) |
| Domain 4.5 | DLT pipeline uses Message Batches API for bulk enrichment at scale |

---

## Task Reference

| Task ID | Component |
|---------|-----------|
| TBD | Set up project structure, CLAUDE.md, .mcp.json |
| TBD | Implement MCP Server #1 (Books API) |
| TBD | Implement MCP Server #2 (Databricks) |
| TBD | Implement MCP Server #3 (Annotations) |
| TBD | Implement multi-agent system (coordinator + 3 subagents) |
| TBD | Build Databricks App (Streamlit, 5 pages) |
| TBD | Set up Unity Catalog schema + Delta tables |
| TBD | Configure Databricks FM + Vector Search |
| TBD | Implement Databricks Workflows (Jobs 1-3) |
| TBD | Set up CI/CD with Claude Code GitHub Actions |
| TBD | Phase 2: Event-driven pipeline upgrade |
