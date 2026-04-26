# Personal To-Do — Long-Term Plan

A todo app is rarely the bottleneck for life overhaul. The features that move the needle are **behavioral, not organizational**. This plan is ordered by leverage on actual task completion, not by technical novelty.

---

## Where the app sits today (v1.4)

**Has:** Tasks (title, description, priority P1-P4, project, due date, recurrence), per-user task lists (Anish/Prerana), color-coded projects in DB, sort by priority/deadline, completed tab, soft-delete with undo, natural-language dates ("tomorrow 3pm"), recurring tasks (daily/weekdays/weekly/monthly), keyboard shortcut Q to add, sidebar feature guide + changelog.

**Lacks:** notifications, mobile-friendly view, keyboard-first navigation (Cmd+K), sub-tasks, daily planning ritual, completion analytics, calendar integration, offline mode, partner-shared tasks, identity/goal cascades.

---

## Phase 1 — Behavioral foundations (highest leverage)

The single most-cited result in the productivity literature is **Gollwitzer's implementation intentions**: when people specify *when* and *where* they'll do something, completion rates roughly double. Bake this into the app.

### 1.1 "When will you do this?" prompt
When adding a task with no due date, show a soft optional prompt asking for a day+time slot. Defaults: today morning / today afternoon / tomorrow morning / pick a time. Skippable.
**Effort:** half a day. **Behavioral basis:** Gollwitzer 1999.

### 1.2 Daily plan ritual
At a configurable hour (default 8am), the Today view becomes a planning screen: "Pick your 3 must-do tasks for today." Drag the rest to Anytime. The act of choosing — not the resulting list — is the thing that works.
**Effort:** 1 day. **Behavioral basis:** Things 3 / Sunsama / "MIT" (most important task) literature.

### 1.3 Yesterday's incompletes roll over visibly
Tasks not completed yesterday appear in Today with a red "yesterday" pill. Creates gentle pressure without nagging.
**Effort:** 2 hours. **Behavioral basis:** loss aversion, momentum bias.

### 1.4 Two-minute rule prompt
On task add, if the user tags `<2min` (or sets a `quick: true` flag), show a soft prompt: "Just do it now?" before saving.
**Effort:** 2 hours. **Behavioral basis:** GTD (David Allen).

### 1.5 Eat the frog
One task per day can be marked "the frog" — surfaced first in Today view with a frog icon. Encourages tackling the most-dreaded thing first.
**Effort:** 3 hours. **Behavioral basis:** Brian Tracy / classic productivity.

---

## Phase 2 — Couples mode (this app's unfair advantage)

You and Prerana already share the app. **No SOTA app does shared accountability well.** This is genuinely novel territory.

### 2.1 Shared / assigned tasks
A task can be assigned to "Anish", "Prerana", or "Both". Visible to whoever it's assigned to. Adds a `shared` boolean and `assignee` field.
**Effort:** half a day.

### 2.2 Daily check-in
30-second end-of-day prompt: what got done, what's blocking, what's tomorrow. Both partners see each other's. Creates ambient awareness without being a meeting.
**Effort:** 1 day.

### 2.3 Sunday weekly review
Guided 5-minute flow: what shipped, what slipped, what's next week's focus. Produces a tiny markdown export so it's archival.
**Effort:** 1 day.

### 2.4 Encouragement nudges
When a partner completes a P1, show a small celebration toast in the other's view. Non-spammy, high-signal.
**Effort:** 2 hours.

### 2.5 Weekly leaderboard (optional, low priority)
Tasks completed this week, side by side. Be careful — competition can backfire if it creates resentment. Make it strictly opt-in.
**Effort:** 2 hours.

---

## Phase 3 — Frictionless input

Friction is the silent killer of every productivity system. If adding a task takes 8 seconds, ideas evaporate before they're captured.

### 3.1 Cmd+K command palette ✦
Linear-style. Add tasks, jump to projects, switch users, complete tasks — everything via keyboard. This single feature transforms the app from "Todoist clone" to "tool I never leave."
**Effort:** 1-2 days.

### 3.2 Sub-tasks (one level only)
Sub-tasks under a parent task. Render indented. Completing all sub-tasks doesn't auto-complete the parent (deliberate friction). One level only — deeper hierarchies become paralysis.
**Effort:** 1 day. Schema: `parent_id` column.

### 3.3 Tags / labels
Lightweight orthogonal grouping (#work, #errands, #high-energy). Multi-tag per task. Filterable.
**Effort:** half a day. Schema: `tags` text column or join table.

### 3.4 Quick capture via Telegram bot
You already have a Telegram bot setup from your other projects. Reuse it: text the bot, task lands in Inbox under the configured user. Captures the 80% of ideas that happen away from the desk.
**Effort:** half a day if reusing existing bot infra.

### 3.5 Email-to-task
Forward an email to a magic address, becomes a task with the email body as description. Stretch goal — only build if Telegram capture isn't enough.
**Effort:** 1 day with a service like CloudMailin or self-hosted.

---

## Phase 4 — Reflection & feedback loops

What gets measured improves — but only if you actually look at it.

### 4.1 Completion stats
Week and month chart: tasks created vs completed. Surfaces overcommitment when the lines diverge. Don't make this a vanity number.
**Effort:** 1 day. Library: Chart.js or hand-rolled SVG.

### 4.2 Streaks for recurring tasks
Each recurring task tracks its consecutive-completion count. "Don't break the chain" (Seinfeld method). Visible streak number on the task.
**Effort:** half a day. Schema: `streak_count` + `last_completed_at` on recurring tasks.

### 4.3 Energy/mood tag on completion
Optional 1-tap log on task complete: low/med/high energy, good/neutral/bad mood. After a few weeks, surfaces patterns ("you complete 3x more before noon").
**Effort:** 1 day for capture + 1 day for the insights view.

### 4.4 Identity tags (Atomic Habits model)
Tag tasks with the identity they reinforce: "I'm becoming a runner," "I'm a writer." James Clear's research suggests identity-based goals stick far better than outcome-based ones.
**Effort:** 1 day. Could be a special tag prefix like `~runner`.

### 4.5 "What you accomplished" weekly digest
Sunday email/notification listing the week's completions, grouped by project. Pure positive reinforcement.
**Effort:** half a day.

---

## Phase 5 — Integrations & polish

### 5.1 Google Calendar one-way push
When a task gets a due date with time, push it to Google Calendar as an event. No two-way sync (way too complex for the value). OAuth setup is the only pain point — actual push logic is ~50 lines.
**Effort:** half a day post-OAuth. **OAuth setup:** 30 min in Google Cloud Console.

### 5.2 Mobile PWA
Add to home screen on iOS/Android, looks like a real app. Push notifications via Web Push API. Service worker for offline mode.
**Effort:** 1-2 days for solid PWA, +1 day for push notifications.

### 5.3 Templates
"Morning routine" inserts 5 pre-defined tasks at once. "New project kickoff" inserts a checklist. Useful for repeated workflows.
**Effort:** half a day.

### 5.4 Offline mode
IndexedDB cache, sync queue when back online. Worth doing if mobile usage is real.
**Effort:** 1-2 days.

### 5.5 API keys for personal automation
Generate a personal API key per user. Lets you wire this into Shortcuts, Raycast, n8n, custom scripts.
**Effort:** half a day.

---

## Phase 6 — Adventurous bets (only if Phases 1-3 are working)

Stuff to try only if the foundation is solid and being used daily.

### 6.1 LLM-powered weekly review
Sunday: Claude reads your completed/incomplete tasks for the week and writes a short summary + asks one reflective question. Could be the missing accountability partner.
**Effort:** 1 day with the Anthropic API.

### 6.2 Auto-scheduling (Motion-style)
LLM looks at your calendar and unscheduled tasks, suggests time blocks. High risk: most auto-scheduling fails because users want control. Build only with strong skepticism.
**Effort:** 3-5 days. **Recommendation:** probably skip unless you really want it.

### 6.3 Voice capture
Whisper-based voice-to-task on mobile PWA. Speak a task, NLP parses date/priority/project.
**Effort:** 2 days.

### 6.4 "Don't add another task" lock
Anti-feature: if you've added more than N tasks today without completing any, the add button greys out and shows "Maybe finish one first?" Forces the system to stay realistic.
**Effort:** 2 hours. **Behavioral basis:** Parkinson's law / list-bloat psychology.

---

## Recommended sequencing

If you want this app to actually change behavior over the next 3 months, here's the order I'd build:

1. **Week 1 (now done):** Completed tab, soft-delete, recurring, NL dates ✓
2. **Week 2:** Daily plan ritual + yesterday-rolls-over (Phase 1.2 + 1.3)
3. **Week 3:** Cmd+K command palette (Phase 3.1) — this is the single biggest UX upgrade
4. **Week 4:** Couples mode — shared tasks + daily check-in (Phase 2.1 + 2.2)
5. **Week 5:** Streaks + completion stats (Phase 4.1 + 4.2)
6. **Then evaluate.** Are you and Prerana actually using it daily? If not, more features won't help — diagnose the real friction first.

---

## Anti-recommendations

Things that look attractive but I'd skip or defer indefinitely:

- **Sub-projects/nested folders** — turns into yak-shaving. Tags handle this better.
- **Custom fields per project** — Notion-style flexibility. Way more cost than value at this scale.
- **Multiple due dates / time ranges** — almost nobody uses this; clutters the UI.
- **Task dependencies / blocking** — only useful in team settings, not personal.
- **Karma points** (Todoist style) — gamification that wears off in 2 weeks.
- **Markdown in descriptions** — tempting but a tarpit. Plain text is fine.
- **Mobile native app** — PWA does 95% of what's needed for 5% of the work.
- **Two-way Google Calendar sync** — order of magnitude harder than one-way push.

---

## Open questions (worth answering before building Phase 2)

1. Should shared tasks be visible to both partners by default, or opt-in per task?
2. Do you want privacy controls — tasks only visible to one user even if both can see the project?
3. Is there a third user case (kid, roommate, work colleague) ever, or strictly two?
4. Web-only for now, or is mobile a hard requirement before further investment?

Decide these before Phase 2 — they shape the data model.
