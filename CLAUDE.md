# Task Tinder

Metacognition-forcing task triage system.

## Architecture

- `server.py` — Flask backend on port 5050. SQLite database (`task_tinder.db`), auto-created on first run with sample data from `sample_tasks.json`.
- `index.html` — Single-page frontend. Vanilla JS, no build step. Swipe gestures, sprint mode, metacognition capture modal.
- `delegations.jsonl` — Append-only log of tasks delegated to Claude. Each line is a JSON object with `task`, `note`, `delegated_at`, `status`.

## Key flows

1. **Triage** — User swipes cards right (queue for sprint), left (skip), or taps delegate (sends to Claude)
2. **Sprint** — 3 queued tasks trigger sprint mode with a running timer
3. **Metacognition capture** — After completing each sprint task, a modal asks "how did you do it?" Method notes are stored in `completions` table
4. **Patterns** — `/api/patterns` returns all method notes with task metadata for pattern analysis

## Database tables

- `tasks` — All tasks with status (pending/completed/delegated/skipped)
- `sessions` — Sprint sessions with completion stats
- `completions` — Method notes + time taken (the learning data)

## Adding new task sources

POST to `/api/tasks` with `{title, source, effort, context}`. Source types: email, meeting, calendar, task, content. To add a new source, just use a new source string — the frontend auto-generates badge styles.

## Delegation flow

When a task is delegated, it's written to `delegations.jsonl`. To pick up delegated work:
1. Read `delegations.jsonl` for entries with `"status": "pending"`
2. Do the work
3. Update the task via `/api/complete` with method notes describing what you did
