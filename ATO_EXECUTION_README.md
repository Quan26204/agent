# ATO Execution Engine patch

## What's added
- `POST /orchestrator/plans/{plan_id}/execute`: starts execution for an approved plan.
- Job lifecycle fields: `output`, `error`, `started_at`, `completed_at`.
- Dependency-aware execution and blocked-job handling.
- Only the `summarization_agent/summarize` handler is enabled. It calls local Ollama (`qwen3:8b`). Research, reminder and email jobs fail safely with an explicit "handler not registered" message until those integrations are implemented.
- Existing chatbot and RAG routes are not replaced.

## Apply
1. Stop the backend (`Ctrl+C`).
2. Back up `backend/chatbot.db` before replacing files.
3. Extract this patch into the project root and allow it to merge/overwrite the `backend` folder.
4. Start the backend using the project's virtual environment:
   `python -m uvicorn backend.main:app --reload`
5. On startup, `create_all` creates missing ATO tables and an additive SQLite migration adds the four new job columns if absent.

## Test in Swagger
1. `POST /orchestrator/plans` to draft a plan.
2. `POST /orchestrator/plans/{plan_id}/approve` to approve it.
3. `POST /orchestrator/plans/{plan_id}/execute` to execute it.
4. `GET /orchestrator/plans/{plan_id}` to inspect each job's status, output and error.

For a summarization job, provide source text in `payload.text` (or `payload.content` / `payload.input`). A dependent summarization job can use the output of its completed dependencies.

## Important limitations
- Execution currently runs synchronously in the API request; keep jobs short. A persistent worker/queue and scheduler are a later step.
- The in-process lock prevents overlapping plan execution in one backend process, but is not a distributed lock across multiple workers/servers.
- No automatic retries, arbitrary code execution, web research, reminders, or email sending are enabled.
- User approval remains required: the execute endpoint rejects plans not in `approved` state.
