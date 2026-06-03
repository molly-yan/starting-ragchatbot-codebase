# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the app (from repo root)
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

The server starts at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Requires a `.env` file at the repo root with `ANTHROPIC_API_KEY=...` (see `.env.example`).

There are no tests in this codebase.

## Architecture

This is a full-stack RAG chatbot. The **backend** is a FastAPI app in `backend/`; the **frontend** is plain HTML/CSS/JS in `frontend/`, served as static files by FastAPI. Course documents live in `docs/` as `.txt` files.

### Query pipeline

Every user message flows through this chain:

```
app.py → RAGSystem → AIGenerator → Claude API (1st call, tool_use)
                                 → VectorStore → ChromaDB
                                 → Claude API (2nd call, final answer)
```

1. `app.py` receives `POST /api/query`, creates a session if needed, delegates to `RAGSystem.query()`.
2. `RAGSystem` fetches conversation history from `SessionManager`, then calls `AIGenerator.generate_response()` with the `search_course_content` tool definition.
3. **First Claude call**: Claude receives the system prompt, conversation history, and the tool. It either answers directly (general knowledge) or returns `stop_reason: "tool_use"`.
4. If tool use: `ToolManager` dispatches to `CourseSearchTool`, which calls `VectorStore.search()`. The store first resolves a fuzzy course name via semantic search on the `course_catalog` ChromaDB collection, then retrieves top-5 content chunks from `course_content` with optional course/lesson filters.
5. **Second Claude call**: tool results are appended to the message history; Claude synthesizes the final answer.
6. The exchange is saved to `SessionManager` (keeps last 2 exchanges). Sources are extracted from `CourseSearchTool.last_sources` and returned alongside the answer.

### Key design points

- **Two ChromaDB collections**: `course_catalog` holds one document per course (title, instructor, lesson links); `course_content` holds chunked lesson text. Both use `all-MiniLM-L6-v2` embeddings.
- **Course name resolution**: fuzzy/partial course names work because course lookup uses vector similarity against `course_catalog` before filtering `course_content`.
- **Tool as the only retrieval path**: there is no direct vector search fallback — all course retrieval goes through Claude's tool call decision. If Claude doesn't call the tool, no RAG retrieval happens.
- **Session history is a formatted string**, not a message array. It's injected into the system prompt, not the messages list.
- **Document format**: course `.txt` files must follow a strict header format (`Course Title:`, `Course Link:`, `Course Instructor:`) followed by `Lesson N: <title>` / `Lesson Link:` blocks. The `DocumentProcessor` parses this format; deviations fall back to treating the whole file as one unchunked document.
- **Chunk IDs** in ChromaDB are `{course_title_underscored}_{chunk_index}`. Re-ingesting the same course title is a no-op (titles are checked against existing IDs before processing).
