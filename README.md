# Task Tinder

A metacognition-forcing task triage system. Swipe through your tasks like cards, sprint through the ones you accept, and — critically — capture *how* you completed them so the system learns your patterns over time.

**The insight:** Most productivity tools track *that* you did something. This one tracks *how* you did it. Over time, you build a personal knowledge base of your own methods, shortcuts, and workflows — which Claude can then use to pre-draft, delegate, and learn your operating style.

Built with Claude Code. By [Logan Currie](https://logancurrie.com).

> **Part of a larger system.** Task Tinder is one interface to [Claude Chief of Staff](https://github.com/loganhc-09/claude-chief-of-staff), the architecture for turning Claude Code into a persistent AI operational layer. See the [full system writeup](https://github.com/loganhc-09/claude-chief-of-staff) for how this fits alongside memory, briefings, and learning loops.

## How It Works

1. **Set your time budget** — 10, 30, or 60 minutes
2. **Swipe through tasks** — queue them for a sprint, skip, or delegate to Claude
3. **Sprint** — once you queue 3 tasks, sprint mode activates with a timer
4. **Capture your method** — after each task, note how you did it (the metacognition moment)
5. **Patterns emerge** — your completions log becomes a personal playbook

### The Metacognition Moment

When you finish a task, a modal asks: *"How did you do it?"*

You might write: "Pulled up the old proposal, adapted the framing for this audience, sent from my phone."

This is the forcing function. You're building a record of your actual workflows — not what a textbook says, but what *you* actually do. Over time, this becomes incredibly valuable for:

- Teaching an AI assistant your patterns
- Identifying which tasks you should always delegate
- Noticing when you're overcomplicating things
- Building templates from your own repeated methods

## Quick Start

```bash
git clone https://github.com/loganhc-09/task-tinder.git
cd task-tinder
pip install flask
python server.py
```

Open [http://localhost:5050](http://localhost:5050). Sample tasks are pre-loaded.

## Connecting to Your Own Data

Task Tinder ships with sample tasks, but the real power comes from connecting it to your actual workflow. The `/api/tasks` endpoint accepts POST requests:

```bash
curl -X POST http://localhost:5050/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Review PR #42", "source": "email", "effort": "30min", "context": "From Sarah, needs review by EOD"}'
```

### Source types
- `email` — inbox items
- `meeting` — follow-ups from calls
- `calendar` — upcoming prep tasks
- `task` — general tasks
- `content` — content creation

### Claude Code delegation

When you delegate a task, it writes to `delegations.jsonl`. Point Claude Code at this file to pick up delegated work:

```markdown
# In your CLAUDE.md
Check delegations.jsonl for tasks delegated from Task Tinder. 
Pick up pending items and mark them complete.
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List pending tasks (optional `?budget=10min`) |
| `/api/tasks` | POST | Add a new task |
| `/api/complete` | POST | Complete a task with method notes |
| `/api/dismiss` | POST | Skip or delegate a task |
| `/api/session` | POST | Start/end a sprint session |
| `/api/stats` | GET | Lifetime stats |
| `/api/patterns` | GET | Your metacognition patterns |

## Stack

- **Frontend:** Vanilla HTML/CSS/JS — no build step, no dependencies
- **Backend:** Python + Flask
- **Database:** SQLite (auto-created on first run)
- **Design:** Outfit + DM Mono fonts, warm neutral palette

## Philosophy

This came from a personal operating system I built with Claude Code. The core idea: your AI assistant should learn from *how you work*, not just *what you tell it to do*. Task Tinder is the interface that captures that learning.

The swipe UX is intentional — it forces fast decisions (do it, skip it, delegate it) rather than letting tasks sit in an infinite backlog. The sprint timer creates urgency. The metacognition capture creates learning.

## License

MIT
