# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

MAI Help You: a MapleStory assistant service (character lookup via Nexon Open API, community board, and an LLM chatbot "메이(MAI)"). Code comments, docstrings, and docs are written in Korean; keep new ones in Korean to match. Use correct MapleStory terminology (스탯/stat, 잠재능력/potential, 스타포스/starforce, 추옵, etc.) and normalize character names when searching.

Design docs live in [docs/](docs/README.md) — check the ADRs in `docs/adr/` before changing architecture.

## Commands

Always run Python commands inside the `.venv` virtualenv (Windows: `.venv\Scripts\activate`). Run everything from the repo root — both servers rely on absolute imports from there.

```bash
# Infra + both servers via Docker (needs env/.env.local with DATABASE_PASSWORD, SECRET_KEY, API keys)
docker compose up

# Local dev (Postgres with pgvector + Redis must be running)
python manage.py migrate
python manage.py runserver            # Django, :8000 (settings default: config.settings.development)
python -m ai_server.main              # FastAPI AI server, :8001 — must be launched as a module

# Python tests (pytest-django; uses config.settings.test → SQLite in-memory, locmem cache)
pytest
pytest tests/test_auth_views.py
pytest tests/test_auth_views.py::TestClassName::test_name

# Frontend (frontend/)
npm run dev        # Vite :5173, proxies /api and /admin to Django :8000
npm run build      # outputs to ../static/dist (served by Django)
npm test           # vitest run
npx vitest run src/api/chatSchema.test.js
npm run lint
```

`pytest`, `pytest-django`, and `pytest-asyncio` are not in `requirements.txt`; install them separately if missing. `asyncio_mode = auto` is set in `pytest.ini`, so async tests need no marker.

## Architecture

Two independent Python servers plus a React SPA (see `docs/project/03_architecture.md`):

```
React (Vite) ──/api/v1/*──▶ Django :8000 ──HTTP POST /generate, /stream──▶ FastAPI ai_server :8001
                              │  Postgres (users, sessions, chat history)    │  LangGraph (stateless)
                              │  Nexon Open API                              │  Gemini / DeepSeek / local LLM, pgvector (RAG)
```

Django owns all conversation state. Each AI request carries `message`, the recent `history` (last 10 non-empty messages, oldest first), and `user_context` (the user's main character: linked `CharacterLink` with `is_main`, else the signup `UserProfile.maple_nickname`). The AI server keeps nothing between requests.

### Django (`config/`, `apps/`, `common/`)
- Settings split: `config/settings/{base,development,production,test}.py`. Env vars are loaded by `config/env_loader.py` (`env/.env.local` first, then root `.env`; existing OS env vars win — this is how docker-compose overrides like `DATABASE_HOST=db` take effect). `ai_server/config.py` duplicates this loading logic for the AI server.
- All API routes are under `/api/v1/<app>/` (`config/urls.py`). The final catch-all route serves the built React `static/dist/index.html` via `apps.core.views.serve_react` (with AdSense config injected), so new API routes must be registered *before* it.
- "Thin views, fat services": business logic belongs in each app's `services.py`; views stay small.
- **Nexon Open API** goes through the shared `common/nexon/` package, which both servers use.
  - Client: retries 429/5xx with backoff. Error classification:
    - 400 `OPENAPI00004` on `/id` or `OPENAPI00003` → `CharacterNotFound`
    - 429 → `ApiRateLimitExceeded`
    - anything else → `NexonApiError` (with `.error_name`)
  - A per-process rate limiter spaces request starts (`NEXON_REQUESTS_PER_SECOND`, default 5 for the low development-key limit).
  - `NexonCache` stores responses in Redis, shared by both servers (OCID 1 day, character data 15 min). It fails open when Redis is down. Django turns it off with `NEXON_CACHE_ENABLED=False` (test settings).
  - Django's `apps/character/nexon/character_service.py` builds the search-page response with `common.nexon.extractors.all_info_extract`. The frontend reads `basic_info`, `stat_info`, and `item_info.item_equipment`, so keep that shape.
- Views/services are async and use `aiohttp` for outbound I/O; get the user with `await request.auser()` (not `request.user`) in async views. `apps/chat/services.py` proxies chat to the AI server, either awaiting `/generate` or relaying `/stream` SSE lines to the client (`StreamRelay` collects tokens/route/sources). It always ends the stream with `data: [DONE]` and saves the answer plus `MessageMetadata` (route, sources, latency). Empty answers are not saved. Because the current frontend ignores `error` events, failures are also sent as a `token` notice (`FAILURE_NOTICE`), which is not persisted.
- Shared cross-app code is in `common/`: custom exceptions (`common/exceptions/`) are converted to responses by `common.middleware.error_handler.ErrorHandlerMiddleware`; a standard response schema is in `common/schemas/response.py`.

### AI server (`ai_server/`)
- `main.py` → `lifespan.py`: builds the main graph (no checkpointer) into `app.state.graph`, then runs registered startup handlers (an APScheduler job for character embeddings at 04:00 KST, Langfuse observability). Handlers are flagged critical/non-critical in `_STARTUP_HANDLERS`; add new init steps there.
- Layout: `api/routes` (HTTP) → `services/chat.py` (request → graph input, graph events → SSE) → `graph`.
- **LangGraph flow** (`graph/builder/main_builder.py`): `route` (structured-output classification into `chat` / `knowledge` / `character` / `character_knowledge`, falls back to `chat` on error) → `knowledge` (RAG subgraph: `rewrite` → `retrieve`) and/or `character` (Nexon subgraph: `extract_character` → `fetch_character`); `character_knowledge` runs both in parallel → `generate` (the only node whose tokens reach the user).
  - Subgraphs have their own builder/nodes/state and an `output_schema` (`RagOutput`, `NexonOutput`). They are invoked *inside* wrapper node functions, not added as nodes directly. Under `astream_events`, a directly added subgraph ignores `output_schema`, and the parallel branch then fails with `InvalidUpdateError`.
  - Don't put a `RetryPolicy` on `generate`: a retry would re-stream tokens the client already received.
  - Character subgraph (`nodes/nexon_nodes.py`):
    - `extract_character` returns a structured `CharacterQuery` (`character_name`, `refers_to_self`, `aspects`) from the last 6 messages, so follow-ups like "그 캐릭터 장비는?" work.
    - `fetch_character` resolves the target with `resolve_target`: a different name in the question wins; otherwise it uses the user's main character from `user_context`, with its OCID when known.
    - It fetches only `/character/basic` plus the endpoints for the chosen aspects (`graph/tools/character_context.py`, max 6). The results are turned into compact Korean markdown, not raw JSON.
    - Lookup failures become guidance text in `character_context` that the answer model relays to the user.
- **SSE contract** (`services/chat.py` docstring): `status`, `route`, `token`, `sources`, `error` JSON events, terminated by `data: [DONE]`. The frontend currently consumes only `token` and `[DONE]`.
- LLMs: nodes never import a provider directly. They use `llm/factory.py`: `get_utility_llm()` (route/rewrite/extract, temperature 0, `LLM_PROVIDER` = `gemini` | `deepseek`) and `get_answer_llm()` (`ANSWER_LLM_PROVIDER`, defaults to `LLM_PROVIDER`; also allows `local` = an OpenAI-compatible server such as vLLM serving `fine_tuned_model/merged_qwen`). Invalid values fail at startup (pydantic `Literal`). `llm/llm_loader.py` (in-process HF pipeline) is only used by `rag/evaluation/`.
- Prompts: all prompt text lives in `prompts/templates.py`, keyed by the `PromptTemplate` enum. The `"gemini"` key is the default text shared by API models; `"local"` is for the local model. Don't inline prompt strings in nodes.
- RAG: `rag/` uses `langchain_postgres.PGVector` with `QwenEmbeddings` (Qwen3-Embedding-0.6B). `vectorstore.build_database()` ingests JSON files (`data/`, `rag_documents/`) plus Redis data. RAG eval lives in `rag/evaluation/`.

### Frontend (`frontend/`)
React 18 + Vite + react-router + styled-components/CSS. API calls go through `src/api/client.js` (axios), and pages use hooks in `src/hooks/`. The `@` alias maps to `src/`. The Vite `base` is `/` in dev and `/static/dist/` in build. The built output in `static/dist/` is committed, so rebuild after frontend changes that should ship.

### Tests
`tests/` holds the Python tests, with shared fixtures (users, profiles, sync/async clients) in `tests/conftest.py`. The test settings strip `pgvector.django`, set `DJANGO_ALLOW_ASYNC_UNSAFE`, and use cache-backed sessions so async views work under SQLite. AI-server tests never call real APIs:
- `tests/test_ai_chat_graph.py` monkeypatches the node helpers (`classify_route`, `rewrite_query`, `search_documents`, `extract_entities`, `get_answer_llm` → `FakeListChatModel`) and drives `/stream` through `httpx.ASGITransport`.
- `tests/test_chat_services.py` fakes `aiohttp.ClientSession` to test the Django relay.
- `tests/test_nexon_client.py` does the same for `common.nexon`. Its fixture zeroes the retry delay and the rate-limiter interval.
