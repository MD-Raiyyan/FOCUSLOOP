# FocusLoop

> **Learn what makes YOU productive.**

FocusLoop is an Android-first personal productivity and behavioral-learning app that turns everyday behavior data into **understanding, experiments, measurement, and improvement**.

---

## 🚀 Current Implementation Status

| Component | Status | Details |
|---|---|---|
| **FastAPI REST Backend** | ✅ Complete | Fully built with SQLAlchemy, SQLite/PostgreSQL, automated migrations |
| **Authentication & Sessions** | ✅ Complete | Argon2id hashing, JWT access tokens, persistent refresh sessions & revocation |
| **Protected Route Security** | ✅ Complete | Strict user isolation via `Depends(get_current_user)`, zero data leakage |
| **Deterministic Behavior Engine** | ✅ Complete | Zero LLM hallucination: completion, delay, and distraction calculations |
| **Pattern Engine V2** | ✅ Complete | Statistical detection with recency decay, contradiction detection, and Inactive vs Resolved semantics |
| **Behavior Profile & Intelligence** | ✅ Complete | Personal profile with strengths, weaknesses, insights, and experiments |
| **Social Profile & Privacy System** | ✅ Complete | Dual-profile architecture with strict backend privacy enforcement |
| **Behavior Progress Curve** | ✅ Complete | 14-day continuous growth trajectory (improving, stable, setback, recovery) |
| **Grading & Level Abstraction** | ✅ Complete | Multi-dimensional progression across 5 milestone tiers |
| **Username-Based Friend Requests** | ✅ Complete | `@username` lookup → pending request → accept/decline flow |
| **AI Context Builder & Chat** | ✅ Complete | Grounded context injection with compassionate, analytical tone |
| **Personalized Onboarding** | ✅ Complete | 5-step onboarding collecting goal, role, focus challenges & schedule |
| **Structured User Context** | ✅ Complete | `UserContext` model driving AI Coach personalization |
| **Task Lifecycle (One-Time vs Daily)** | ✅ Complete | `frequency`: `once` / `daily`, per-day occurrence with idempotent check-ins |
| **Task Occurrence Idempotency** | ✅ Complete | `UniqueConstraint(task_id, date)` + upsert logic in `POST /checkins` |
| **PostgreSQL & Database Layer** | ✅ Complete | Full schema, 4 Alembic migrations, connection pooling, SQLite fallback |
| **Time-Bounded Experiment Evaluation** | ✅ Complete | Pre-experiment baseline window vs. observation window; no lifetime dilution; `inconclusive` on sparse data |
| **Experiment Lifecycle Enforcement** | ✅ Complete | `suggested → active → completed`; status-gated evaluation; profile refresh on completion |
| **Experiment Generator** | ✅ Complete | Pattern-driven suggestions; idempotent (no duplicate experiment titles per user) |
| **Lab Screen (Experiment UI)** | ✅ Complete | Crash fixed; status-aware hero banner, Start/Evaluate/Results display |
| **Automated Test Suite** | ✅ Passing | **121 backend tests passing** (Auth, behavior patterns v2 semantics, AI context, task lifecycle, social, time-bounded experiments) |
| **Mobile Frontend (React Native/Expo)** | ✅ Connected | All major endpoints integrated end-to-end; Lab screen stable; physical Android testing verified |

---

## 1. Project Overview

FocusLoop is being developed for the **ASYNC'26 Wellness & Lifestyle Hackathon — Track 2**.

The core idea is not to build another productivity dashboard. FocusLoop is designed as a **closed-loop behavioral system**:

```text
Goal
  ↓
Habit / Task
  ↓
Collect Evidence
  ↓
Measure
  ↓
Understand Pattern
  ↓
AI Explanation
  ↓
Personalized Experiment
  ↓
Measure Result
  ↓
Learn
  ↓
Next Action
```

FocusLoop should help users answer questions such as:

- When am I most productive?
- When do I tend to delay starting?
- What usually happens during my procrastination episodes?
- Which interventions appear to help me?
- Did the last experiment actually improve my behavior?
- What has FocusLoop learned about my working patterns?

FocusLoop should **not** label users as good/bad, lazy, disciplined, etc. It should describe observed patterns with appropriate uncertainty.

---

# 2. Product Vision

### Vision

> **From tracking behavior to changing behavior.**

FocusLoop collects purpose-driven evidence, identifies behavioral patterns, explains those patterns using AI, proposes small personalized experiments, measures their results, and uses those results to improve future recommendations.

### Main Differentiator

Most productivity apps stop at:

```text
Track → Display
```

FocusLoop aims to do:

```text
Track
  ↓
Understand
  ↓
Experiment
  ↓
Measure
  ↓
Learn
  ↓
Adapt
```

---

# 3. Core MVP

The hackathon MVP should prove one complete loop rather than trying to implement every possible feature.

### MVP flow

```text
1. User sets a goal
2. User creates 2–3 habits/tasks
3. FocusLoop collects task/check-in evidence
4. FocusLoop collects supporting behavioral evidence
5. Behavior Engine calculates deterministic metrics
6. Pattern Engine identifies a recurring pattern
7. AI explains the pattern using structured evidence
8. AI proposes a measurable experiment
9. User follows the experiment
10. FocusLoop measures before vs. after
11. System records the result
12. Future recommendations use the learned result
```

### Core MVP features

- Goal onboarding
- Habit/task creation
- Task check-ins
- User-triggered procrastination mode
- Basic Android app-usage evidence where technically available
- Basic sleep/context data where available; otherwise clearly marked as estimated or optional
- Deterministic behavior metrics
- Pattern detection
- Behavior profile
- AI Context Builder
- AI-generated behavioral explanation
- Personalized experiment
- Experiment result measurement
- Basic behavioral learning/update
- Dashboard/insight screen

---

# 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Mobile | React Native | Android mobile application |
| Mobile framework | Expo | React Native development/tooling |
| Mobile language | TypeScript | Application language |
| Initial testing | Expo Go | Physical-device development |
| Native fallback | Expo Development Build | Required when Expo Go cannot provide a needed native capability |
| Editor | VS Code | Development |
| AI coding | GitHub Copilot | Coding assistance |
| Backend | Python | API, analytics and behavior engine |
| API | FastAPI | REST backend |
| Database | PostgreSQL | Primary database |
| Analytics | Python + SQL | Deterministic metrics/patterns |
| Optional analytics | Pandas | Prototyping/analysis |
| AI | LLM API | Explanations, hypotheses, recommendations |
| Future memory | pgvector | Optional behavioral memory/RAG |
| Version control | Git + GitHub | Collaboration and source control |
| Mobile testing | Physical Android phones | No emulator required initially |

### Important development decision

Initially:

- **No Android Studio**
- **No Android emulator**
- **No EAS requirement**
- **No RAG**
- **No per-user LLM fine-tuning**
- **No complex ML**

If native Android functionality is unavailable in Expo Go, use an Expo Development Build.

---

# 5. System Architecture

```text
                         ┌─────────────────────┐
                         │     User Goal       │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Habits / Tasks      │
                         └──────────┬──────────┘
                                    ↓
                     ┌─────────────────────────────┐
                     │ Evidence Collection         │
                     │                             │
                     │ • Task check-ins            │
                     │ • Screen/app usage          │
                     │ • Sleep/context             │
                     │ • Procrastination episodes  │
                     └──────────────┬──────────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Mobile State        │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ FastAPI Backend     │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ PostgreSQL          │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Behavior Engine     │
                         └──────────┬──────────┘
                                    ↓
                   ┌─────────────────────────────────┐
                   │ Metrics / Patterns / Profile   │
                   └────────────────┬────────────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ AI Context Builder  │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ LLM / AI            │
                         └──────────┬──────────┘
                                    ↓
                    ┌────────────────────────────┐
                    │ Insight / Experiment       │
                    └─────────────┬──────────────┘
                                  ↓
                    ┌────────────────────────────┐
                    │ Measure Experiment Result  │
                    └─────────────┬──────────────┘
                                  ↓
                    ┌────────────────────────────┐
                    │ Update Behavior Profile    │
                    └─────────────┬──────────────┘
                                  │
                                  └──────→ Next Action
```

---

# 6. Repository Structure

```text
FOCUSLOOP/
│
├── mobile/
│   ├── app/
│   │   ├── (tabs)/
│   │   ├── onboarding/
│   │   ├── tasks/
│   │   ├── insights/
│   │   ├── experiments/
│   │   └── chat/
│   │
│   ├── components/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── constants/
│   ├── utils/
│   ├── assets/
│   ├── app.json
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── users.py
│   │   │   ├── tasks.py
│   │   │   ├── checkins.py
│   │   │   ├── behavior.py
│   │   │   ├── experiments.py
│   │   │   └── chat.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── behavior/
│   │   │   ├── metrics.py
│   │   │   ├── patterns.py
│   │   │   └── profile.py
│   │   ├── ai/
│   │   │   ├── context_builder.py
│   │   │   ├── prompts.py
│   │   │   └── llm.py
│   │   └── experiments/
│   │       ├── generator.py
│   │       └── evaluator.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── product/
│   └── hackathon/
│
├── .gitignore
├── README.md
└── LICENSE
```

The structure can evolve, but the separation between `mobile/` and `backend/` should remain.

---

# 7. Mobile Architecture

The mobile app is responsible for:

- User interface
- Onboarding
- Habit/task management
- Task check-ins
- Procrastination-mode controls
- Displaying insights
- Displaying experiments
- AI companion interface
- Collecting permitted device evidence
- Local state
- Syncing with the backend

Conceptually:

```text
React Native UI
      ↓
Screens / Components
      ↓
Hooks / State
      ↓
Services
      ↓
API Client
      ↓
FastAPI
```

The mobile application should not become the source of truth for behavioral analysis.

---

# 8. Backend Architecture

The backend is responsible for:

- API requests
- Data validation
- Database access
- Metric calculation
- Pattern detection
- Behavior profiles
- AI context generation
- LLM calls
- Experiment generation
- Experiment evaluation
- Behavioral learning updates

Conceptually:

```text
API Layer
   ↓
Service Layer
   ↓
Behavior / AI / Experiment Engines
   ↓
PostgreSQL
```

---

# 9. Data Collection Model

FocusLoop follows a **purpose-driven minimum-data principle**.

The user should provide important labels manually while the system collects supporting evidence where appropriate.

## Primary evidence sources

### 1. Tasks/Habits

Intentional data:

- What the user planned
- Planned time
- Completion status
- Completion time
- Optional duration
- Optional reason/context

### 2. Screen/App Usage

Supporting observational evidence:

- App usage duration
- Relevant time windows
- Activity during task/procrastination periods

Screen usage alone should not automatically mean procrastination.

```text
YouTube used for 20 minutes
```

does not automatically mean:

```text
User procrastinated for 20 minutes
```

### 3. Sleep / Context

Optional contextual information.

If estimated rather than measured through a supported health/wearable source, it must be clearly labeled as estimated.

### 4. User-triggered Procrastination Mode

The user can explicitly say:

```text
I'm procrastinating
```

FocusLoop starts an observation window.

Example:

```text
7:05 PM
     ↓
Procrastination mode
     ↓
YouTube: 12 min
Instagram: 8 min
Chrome: 5 min
     ↓
7:30 PM
     ↓
Task started
```

This gives FocusLoop a user-confirmed behavioral event.

---

# 10. Procrastination Model

FocusLoop distinguishes between:

### Confirmed procrastination

The user explicitly triggers:

```text
I'm procrastinating
```

### Inferred/estimated procrastination

The system identifies a possible pattern based on:

- Planned task timing
- Start delay
- Screen/app usage
- Previous patterns
- Context such as sleep
- Historical behavior

The second category must be communicated as an estimate.

Use:

- "Possible procrastination pattern"
- "Observed during this window"
- "Your data suggests..."
- "Associated with..."
- "This may indicate..."

Avoid claiming causality without evidence.

---

# 11. Behavior Engine

The Behavior Engine is the analytical core of FocusLoop.

The initial implementation should be:

- Deterministic
- Explainable
- Rule-based
- Statistical
- Based on Python and SQL

Do not begin with machine learning.

## Example metrics

```text
Task completion rate
Start delay
Average start delay
Completion consistency
Focus ratio
Distraction ratio
Time-of-day performance
Procrastination episode duration
App usage during relevant windows
Sleep/context correlation
Experiment improvement
```

Example:

```text
12 planned tasks
9 completed
3 missed

Completion rate = 75%

Average start delay = 31 minutes

Evening completion rate = 82%
Afternoon completion rate = 43%
```

Numerical calculations should be performed by the application/backend, not by the LLM.

---

# 12. Pattern Detection

The Pattern Engine converts metrics into meaningful patterns.

Example:

```text
Pattern:

Tasks planned between 2 PM and 5 PM
have a higher average start delay.

Sample:
12 tasks

Confidence:
Moderate
```

Potential pattern types:

```text
time_of_day
start_delay
completion_rate
distraction_association
procrastination_sequence
task_type
experiment_result
sleep_context
successful_intervention
```

A pattern should include:

- Pattern type
- Description
- Confidence
- Sample size
- First detected date
- Last detected date
- Supporting metrics
- Status

Do not declare strong personal patterns from tiny amounts of data.

---

# 13. Behavior Profile

FocusLoop maintains a current representation of what has been learned about the user.

Example:

```json
{
  "best_focus_window": "19:00-21:00",
  "worst_focus_window": "14:00-17:00",
  "average_focus_duration": 31,
  "task_completion_rate": 0.74,
  "common_distraction": "Instagram",
  "successful_interventions": [
    "evening_scheduling",
    "micro_tasks"
  ]
}
```

The profile should evolve as new evidence arrives.

It should not be treated as a permanent personality label.

---

# 14. Suggested Database Model

Initial core tables:

```text
users
tasks
task_checkins
procrastination_events
screen_usage
sleep_records
behavior_metrics
behavior_patterns
behavior_profiles
experiments
experiment_results
conversations
messages
```

## `users`

```text
id
created_at
updated_at
```

## `tasks`

```text
id
user_id
name
description
planned_time
frequency
active
created_at
updated_at
```

## `task_checkins`

```text
id
task_id
user_id
date
status
completed_at
duration_minutes
created_at
```

Possible status:

```text
done
partial
missed
```

## `procrastination_events`

```text
id
user_id
started_at
ended_at
duration_seconds
user_confirmed
context
created_at
```

## `screen_usage`

```text
id
user_id
app_identifier
started_at
ended_at
duration_seconds
source
created_at
```

## `behavior_metrics`

```text
id
user_id
metric_type
metric_value
time_window_start
time_window_end
metadata
created_at
```

## `behavior_patterns`

```text
id
user_id
pattern_type
description
confidence
sample_size
first_detected
last_detected
status
supporting_metrics
created_at
```

## `behavior_profiles`

```text
user_id
profile
model_version
updated_at
```

## `experiments`

```text
id
user_id
title
description
hypothesis
start_date
end_date
target_metric
baseline_value
status
created_at
```

## `experiment_results`

```text
id
experiment_id
metric_name
before_value
after_value
change_value
result_summary
created_at
```

---

# 15. AI Architecture

FocusLoop should **not** train a separate LLM for each user.

Instead:

```text
Shared LLM
    +
User-specific behavioral context
    ↓
Personalized response
```

The backend prepares relevant context before calling the LLM.

---

# 16. AI Context Builder

The AI Context Builder selects relevant structured information rather than sending the entire database to the model.

Example:

```python
def build_ai_context(user_id):
    metrics = get_recent_metrics(user_id)
    patterns = get_active_patterns(user_id)
    profile = get_behavior_profile(user_id)

    return {
        "metrics": metrics,
        "patterns": patterns,
        "profile": profile,
    }
```

Later it may also include:

- Relevant experiment history
- Behavioral memories
- Recent conversation context
- User feedback

---

# 17. AI Responsibilities

The LLM can:

- Explain detected patterns
- Summarize behavioral evidence
- Generate personalized hypotheses
- Suggest experiments
- Explain why an experiment was suggested
- Discuss uncertainty
- Answer questions about behavioral data
- Provide conversational coaching

The LLM should not be responsible for:

- Core numerical calculations
- Inventing measurements
- Treating assumptions as facts
- Diagnosing psychological conditions
- Making unsupported causal claims

---

# 18. Conversational AI

FocusLoop can eventually provide a behavioral companion.

Example questions:

```text
Why do you think I procrastinate more in the afternoon?

Show me the pattern you're seeing.

Why did you give me this experiment?

Did the last experiment work?

What have you learned about me?

When am I most productive?

What usually distracts me?

What changed this week?
```

Architecture:

```text
User
 ↓
Chat Interface
 ↓
FastAPI Chat API
 ↓
Conversation Manager
 ↓
AI Context Builder
 ↓
PostgreSQL
 ↓
Behavior Profile
 ↓
Optional Behavioral Memory
 ↓
LLM
 ↓
AI Response
```

---

# 19. Conversation Storage

Conversation history is different from behavioral memory.

Suggested tables:

```text
conversations
messages
```

A conversation may contain:

```text
User:
Why am I procrastinating today?

AI:
Your recent data shows...
```

The conversation itself should not automatically become a behavioral fact.

User feedback should be treated as subjective/user-reported context unless supported by measured evidence.

---

# 20. RAG / Vector Memory

RAG is **not part of the initial MVP**.

FocusLoop's core data is structured and temporal, so:

```text
PostgreSQL
+
Behavior Engine
+
AI Context Builder
```

is sufficient initially.

Later, behavioral memories can be embedded using PostgreSQL + pgvector.

Example:

```text
"Moving difficult technical tasks to the evening
increased completion from 52% to 76% over 3 days."
```

Future architecture:

```text
PostgreSQL exact facts
        +
Behavioral vector memories
        ↓
Hybrid retrieval
        ↓
AI Context Builder
        ↓
LLM
```

Do not embed every raw event.

---

# 21. Experiment Engine

Experiments are central to FocusLoop.

An experiment should have:

```text
Hypothesis
Intervention
Observation period
Target metric
Baseline
Result
```

Example:

```text
Hypothesis:
Evening scheduling may reduce task start delay.

Intervention:
Move difficult tasks from 3 PM to 7 PM.

Duration:
3 days

Target:
Average start delay
```

Before:

```text
42 minutes
```

After:

```text
19 minutes
```

The system should report the measured change without claiming that the experiment proves causality.

---

# 22. API Structure

Initial API can include:

```text
GET  /health

POST /users
GET  /users/{user_id}

GET  /tasks
POST /tasks
PATCH /tasks/{task_id}
DELETE /tasks/{task_id}

POST /checkins
GET  /checkins

POST /procrastination/start
POST /procrastination/end

POST /usage
GET  /usage

GET  /behavior/metrics
GET  /behavior/patterns
GET  /behavior/profile

POST /experiments
GET  /experiments
GET  /experiments/{id}
POST /experiments/{id}/result

POST /chat
GET  /conversations
GET  /conversations/{id}/messages
```

The API will evolve during implementation.

---

# 23. Security & Environment Variables

Never commit secrets to GitHub.

Examples:

```text
DATABASE_URL
LLM_API_KEY
JWT_SECRET
OTHER_API_KEYS
```

Use:

```text
.env
```

locally.

Commit:

```text
.env.example
```

Example:

```env
DATABASE_URL=
LLM_API_KEY=
JWT_SECRET=
```

`.env` must be included in `.gitignore`.

---

# 24. Git Workflow

GitHub is the shared source of truth.

Recommended branches:

```text
main
│
├── feature/mobile-ui
├── feature/backend-api
├── feature/behavior-engine
└── feature/ai
```

Do not have two AI coding agents simultaneously rewrite the same files.

Example division:

### Developer 1

Primarily:

```text
mobile/
```

### Developer 2

Primarily:

```text
backend/
```

Use focused commits:

```text
feat: add onboarding screen
feat: add task API
feat: add task check-ins
feat: add completion metrics
feat: add pattern detector
feat: add AI context builder
feat: add experiment engine
```

---

# 25. AI Coding Agent Rules

Do not give an AI agent:

```text
Build the entire FocusLoop app.
```

Give small bounded tasks.

Example:

```text
Implement the FocusLoop onboarding screen.

Do not modify backend files.
Do not change the project architecture.
Use existing components where possible.
```

Backend example:

```text
Implement POST /tasks and GET /tasks.

Do not modify the mobile application.
Follow the existing FastAPI structure.
Add tests for the endpoints.
```

Behavior example:

```text
Implement task completion rate and average start delay.

Use deterministic Python logic.
Do not use an LLM.
Add unit tests.
```

---

# 26. Development Roadmap

## Phase 1 — Environment

- Install Node.js LTS
- Install VS Code
- Install Git
- Install Expo Go
- Verify GitHub repository
- Create project structure

## Phase 2 — Mobile Foundation

- Create Expo project
- Run on physical Android phone
- Create navigation
- Create basic theme
- Create reusable components

## Phase 3 — Onboarding

- Welcome screen
- Goal selection
- Habit creation
- Initial preferences

## Phase 4 — Task System

- Create task
- Edit task
- Pause/resume task
- Task check-in
- Completion status

## Phase 5 — Backend

- FastAPI setup
- PostgreSQL setup
- Database models
- CRUD APIs
- Mobile/backend connection

## Phase 6 — Behavior Engine

- Completion rate
- Start delay
- Time-of-day analysis
- Basic consistency metrics
- Procrastination episode metrics

## Phase 7 — Pattern Engine

- Detect recurring patterns
- Calculate confidence
- Track sample size
- Store patterns
- Create behavior profile

## Phase 8 — Procrastination

- User-triggered procrastination mode
- Observation window
- Activity evidence
- End episode
- Store event

## Phase 9 — Android Usage Evidence

- Investigate required Android APIs
- Test usage statistics
- Integrate native functionality if required
- Use Expo Development Build if Expo Go is insufficient

## Phase 10 — AI

- AI Context Builder
- Prompt structure
- LLM API integration
- Evidence-grounded explanations
- Experiment recommendations

## Phase 11 — Experiment Engine

- Create experiment
- Baseline metric
- Track experiment
- Calculate result
- Update profile

## Phase 12 — Conversational AI

- Chat interface
- Conversation storage
- Behavioral context
- AI explanations
- User feedback

## Phase 13 — Demo

- Seed/demo data
- Complete end-to-end flow
- Test error states
- Prepare hackathon presentation
- Prepare backup demo if needed

---

# 27. MVP Priority

### P0 — Must work

```text
Goal
↓
Task
↓
Check-in
↓
Metrics
↓
Pattern
↓
AI explanation
↓
Experiment
↓
Result
```

### P1 — Important

- Procrastination mode
- Screen usage evidence
- Behavior profile
- Conversational AI

### P2 — Later

- RAG/vector memory
- Health Connect
- Wearables
- Calendar integration
- More advanced personalization
- Advanced machine learning
- Expanded behavioral memory

---

# 28. Explicitly Out of Scope for MVP

Do not spend hackathon time on:

- Per-user LLM fine-tuning
- Full RAG infrastructure
- Complex ML models
- Psychological diagnosis
- 24/7 surveillance
- Location tracking
- Nutrition tracking
- Large wearable ecosystem
- Social leaderboards
- Complex gamification
- Universal productivity score
- Kubernetes
- Kafka
- Microservices
- Graph databases
- Complex cloud infrastructure

---

# 29. Privacy Principles

### Purpose-driven collection

Only collect data that helps answer a meaningful behavioral question.

### User control

The user should decide what FocusLoop tracks where practical.

### Minimal surveillance

Do not attempt to monitor every aspect of a person's life.

### Context matters

App identity alone does not prove distraction.

### Uncertainty matters

Distinguish:

```text
Observed
```

from:

```text
User-reported
```

from:

```text
Estimated
```

from:

```text
AI hypothesis
```

### No psychological diagnosis

FocusLoop is a productivity/behavioral-learning system, not a medical or psychological diagnostic system.

---

# 30. Responsible AI Rules

AI responses should:

1. Be grounded in measured data.
2. Clearly distinguish evidence from interpretation.
3. Avoid unsupported causal claims.
4. Avoid psychological diagnoses.
5. Avoid presenting uncertain patterns as certain.
6. Explain why recommendations were made.
7. Use deterministic backend metrics where possible.
8. Never invent measurements.
9. Respect the user's ability to disagree with an interpretation.

### Good

> "Your recent data suggests that tasks scheduled between 2 PM and 5 PM have a higher average start delay."

### Avoid

> "You are naturally unproductive in the afternoon."

---

# 31. Demo Strategy

The strongest hackathon demo should tell one complete story.

Example:

```text
User:
"I want to become more consistent with studying."

        ↓

Creates:
"Study DSA — 7 PM"

        ↓

FocusLoop collects:
Task completion
Start delay
Screen usage
Procrastination episodes

        ↓

Behavior Engine:

Afternoon start delay: 42 min
Evening start delay: 18 min

        ↓

Pattern:

Evening tasks start more consistently.

        ↓

AI:

"Your recent data suggests that
evening scheduling may work better
for this type of task."

        ↓

Experiment:

Move difficult study tasks to 7 PM
for 3 days.

        ↓

Result:

Average start delay
42 min → 19 min

        ↓

FocusLoop:

"During this experiment,
start delay decreased by 23 minutes."

        ↓

Learn:

Evening scheduling becomes a
candidate successful intervention.
```

Core demo message:

> **FocusLoop doesn't just tell you what happened. It helps you test what might work.**

---

# 32. Success Criteria

The MVP is successful if a judge can see:

```text
1. A user goal
        ↓
2. Real or controlled evidence
        ↓
3. A measurable behavioral pattern
        ↓
4. An evidence-grounded AI explanation
        ↓
5. A personalized intervention
        ↓
6. A measurable result
        ↓
7. A learning/update for the next recommendation
```

The core question is:

> **Can FocusLoop close the loop between behavior, understanding, action, and measurable improvement?**

---

# 33. Local Development

## Mobile

From the `mobile/` directory:

```bash
npm install
npx expo start
```

Scan the QR code using Expo Go on the Android phone.

## Backend

From the `backend/` directory:

```bash
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

The exact commands may evolve as implementation progresses.

---

# 34. Testing Strategy

## Mobile

Test on physical Android devices.

Important tests:

- Onboarding
- Task creation
- Check-in
- Navigation
- API failures
- Offline behavior where applicable

## Backend

Test:

- Metrics
- Pattern detection
- API endpoints
- Experiment evaluation
- AI context construction

## Behavior Engine

Behavior calculations should be tested with known input/output examples.

Example:

```text
Input:
4 tasks
3 completed

Expected:
Completion rate = 75%
```

The Behavior Engine should be deterministic.

---

# 35. Current Architecture Decision

### Chosen

```text
React Native
+
Expo
+
TypeScript
+
FastAPI
+
PostgreSQL
+
Python Behavior Engine
+
LLM API
+
Optional pgvector later
+
GitHub
```

### Development

```text
VS Code
+
GitHub Copilot
+
Antigravity
+
Physical Android phones
```

### Avoid initially

```text
Android Studio
Android Emulator
Kubernetes
Kafka
Microservices
ML training
RAG
Complex vector infrastructure
```

---

# 36. Architecture Principle

Keep the system simple:

```text
Mobile
   ↓
API
   ↓
Database
   ↓
Behavior Engine
   ↓
AI Context Builder
   ↓
LLM
   ↓
Experiment Engine
```

Every additional technology must have a clear reason to exist.

---

# 37. Final Product Loop

```text
┌──────────────────────────────┐
│          USER GOAL           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       HABIT / TASK           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       COLLECT EVIDENCE       │
│                              │
│ Tasks • Usage • Sleep •      │
│ Procrastination • Context    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│      BEHAVIOR ENGINE         │
│                              │
│ Metrics • Patterns • Profile │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│      AI CONTEXT BUILDER      │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│             AI               │
│                              │
│ Explain • Hypothesize •      │
│ Recommend                    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│         EXPERIMENT           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│          MEASURE             │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│           LEARN              │
└──────────────┬───────────────┘
               │
               └──────────────→ NEXT ACTION
```

---

# 38. Current Implementation & Progress Report

FocusLoop's backend is **100% complete, fully implemented with FastAPI and SQLAlchemy, and verified with 23 automated unit/integration tests**.

The project is divided between collaborators:
* **Backend (Complete):** FastAPI REST API, Argon2id & JWT Authentication, Persistent Refresh Sessions, Deterministic Behavior Engine, Pattern Detection, Social & Personal Profile System, AI Context Builder, and SQLite/PostgreSQL Database.
* **Frontend (In Progress):** React Native / Expo application being built by the frontend collaborator to connect to these endpoints.

---

### A. Authentication, Registration & Persistent Login Architecture

FocusLoop provides a complete, production-ready, persistent authentication system that allows users to remain logged in across application restarts, device reboots, and app backgrounding.

```text
User opens FocusLoop App
        ↓
Check local stored tokens (Expo SecureStore)
        ↓
Is Access Token still valid?
  ├── YES ──→ Proceed to Main Application
  └── NO  ──→ Send Refresh Token (POST /api/v1/auth/refresh)
                ↓
              Is Refresh Session valid & unrevoked?
                ├── YES ──→ New Access Token issued ──→ Main Application (Silent renewal)
                └── NO  ──→ Clear local tokens ──→ Show Login / Sign Up screen
```

#### 1. Security & Cryptographic Foundation
* **Password Hashing:** Passwords are hashed using the state-of-the-art **Argon2id** algorithm via `argon2-cffi`. Plaintext passwords and raw hashes are never exposed in any API response or logs.
* **Short-Lived Access Tokens:** Signed with HMAC-SHA256 (`HS256`) using configuration-driven secrets (`JWT_SECRET_KEY`). Default expiration is 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`).
* **Long-Lived Persistent Refresh Sessions:** Refresh tokens are 256-bit cryptographically secure random URLs (`secrets.token_urlsafe(32)`). They are stored server-side only as **SHA-256 hashes** (`token_hash`) in the `refresh_sessions` table with configurable validity (`REFRESH_TOKEN_EXPIRE_DAYS=30`).
* **Explicit Server-Side Revocation:** When the user explicitly logs out via `POST /api/v1/auth/logout`, their session entry in the database is marked with `revoked_at = utcnow`. Any subsequent attempt to use that refresh token is rejected with `401 Unauthorized`.
* **Zero Frontend Identity Spoofing:** Endpoints such as `GET /api/v1/profile/me` identify the user strictly from the verified JWT payload (`sub: user_id`). Query parameters or request bodies attempting to pass another user's ID are ignored.
* **Resource Ownership & Cross-User Isolation:** Tasks, check-ins, procrastination logs, and screen usage sessions are strictly scoped to `current_user.id`. Authenticated User A cannot view, update, or delete User B's resources (returns `404 Not Found`).

---

### B. The Profile & Privacy System (Feature Capsule)

FocusLoop strictly separates **internal behavioral intelligence** from **publicly shareable progress metrics**:

#### 1. Internal Behavioral Intelligence (Private by Default)
* `behavior_score` (0–100): Numerical representation of the user's current behavioral state (synthesizing 45% completion rate, 35% initiation promptness, 20% distraction resistance).
* `current_level`: Multi-dimensional behavioral milestone (e.g., *Level 2 — Pattern Explorer*).
* `behavioral_patterns`: Detected recurring focus friction (e.g., Afternoon Focus Friction, Start Delay Resistance).
* `strengths`, `weaknesses`, `insights`: Sensitive internal diagnostic observations.
* `experiments`: Detailed experiment hypotheses, target metrics, and raw session data.
* **Privacy Guarantee:** These fields are **never leaked** to friends or public endpoints unless explicitly enabled by the user.

#### 2. Social Progress Profile (Public by Default)
Designed around the question *"How is this person improving?"* rather than *"What does the system know about their behavior?"*:
* `improvement_score` (0–100): Measures positive trajectory and growth over time rather than absolute performance.
* `experiment_effectiveness` (0–100): Measures how successfully the user applies behavioral interventions based on verified experiment outcomes.
* `consistency` (0–100): Measures behavioral reliability, task follow-through, and start-time stability across days.
* `progress_curve`: Continuous 14-day behavioral trajectory visualization identifying dynamic states (`improving`, `stable`, `setback`, `recovery`).
* `milestones`: Shareable accomplishments (e.g., streaks, focus milestones, completed sessions).

#### 3. Privacy Configuration Defaults & Independent Controls

| Metric | Default Visibility | Exposed to Friends by Default? |
|:---|:---:|:---:|
| **Current Level** | `Private` | ❌ No |
| **Behavior Score** | `Private` | ❌ No |
| **Behavioral Patterns** | `Private` | ❌ No |
| **Improvement Score** | `Public` | ✅ Yes |
| **Experiment Effectiveness** | `Public` | ✅ Yes |
| **Consistency** | `Public` | ✅ Yes |
| **Behavior Progress Curve** | `Public` | ✅ Yes |

* **Zero-Leakage Backend Enforcement:** When a metric is private, it is completely omitted (`null`) in the API response—never returned with a `{ visible: false }` leak.
* **Independent Toggles:** Changing one visibility setting (e.g., enabling `behavior_score`) never automatically leaks other private metrics.

#### 4. Decoupled Grading & Level Abstraction (`app/behavior/grading.py`)
Rather than hardcoding an arbitrary formula or rigid XP game mechanic, grading is defined as an extensible `GradingStrategy` evaluating multi-dimensional progress:
* **Level 1 — Foundation:** Initial baseline establishment and routine observation.
* **Level 2 — Pattern Explorer:** Friction windows and procrastination triggers mapped.
* **Level 3 — Momentum Builder:** Routine stabilization and active focus interventions.
* **Level 4 — Habit Optimizer:** High reliability across focus windows and rapid setback recovery.
* **Level 5 — Deep Focus Master:** Peak cognitive resilience and autonomous regulation.

---

### C. Complete API Endpoint Reference (For Frontend Integration)

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

#### 1. Authentication Endpoints (`/api/v1/auth`)

| Endpoint | Method | Auth Required | Description | Request Body / Payload |
|---|---|:---:|---|---|
| `/api/v1/auth/register` | `POST` | No | Creates new account, hashes password via Argon2id, initializes default profile & privacy settings, returns tokens | `{ "email": "user@focusloop.com", "password": "...", "name": "...", "username": "..." }` |
| `/api/v1/auth/login` | `POST` | No | Authenticates email/username & password, records persistent session, returns tokens | `{ "email": "user@focusloop.com", "password": "..." }` |
| `/api/v1/auth/refresh` | `POST` | No | Silent renewal: exchanges valid refresh token for fresh access token | `{ "refresh_token": "..." }` |
| `/api/v1/auth/logout` | `POST` | Optional | Revokes refresh token in database; clears persistent session | `{ "refresh_token": "..." }` |
| `/api/v1/auth/me` | `GET` | **Bearer** | Returns authenticated user's basic identity (`id`, `name`, `username`, `email`) | *None* |

#### 2. Profile & Visibility Endpoints (`/api/v1/profile`)
All protected endpoints require the header `Authorization: Bearer <access_token>`.

* `GET /api/v1/profile/me`: Returns owner's complete personal profile (including private intelligence, all metrics, strengths, weaknesses, and curve). Identity is resolved strictly from the verified JWT.
* `GET /api/v1/profile/visibility`: Returns user's current visibility preferences.
* `PUT /api/v1/profile/visibility` or `PATCH /api/v1/profile/visibility`: Updates visibility preferences (independent booleans).
* `GET /api/v1/profile/curve?days=14`: Returns 14-day continuous behavior progress curve points.
* `GET /api/v1/profile/users/{user_id}`: Returns social profile for another user, strictly filtered by their privacy settings.

#### 3. Social & Friends Endpoints (`/api/v1/social`)
* `GET /api/v1/social/friends`: List confirmed friends for current user.
* `POST /api/v1/social/friends`: Add a friend (`{ "friend_id": "uuid" }`).
* `DELETE /api/v1/social/friends/{friend_id}`: Remove a friend.
* `GET /api/v1/social/friends/{friend_id}/profile`: Convenience endpoint to view friend's social profile.

#### 4. Behavioral Engine & Summary (`/api/v1/behavior`)
* `GET /api/v1/behavior/summary`: Deterministic summary of completion rate, start delay, best/worst windows, and active patterns.
* `GET /api/v1/behavior/patterns`: Detected statistical patterns with confidence levels.
* `GET /api/v1/behavior/profile`: Dynamic learned behavior profile.
* `POST /api/v1/behavior/refresh`: Force recalculation of metrics and profile.

#### 5. Habits, Tasks & Check-ins (`/api/v1/tasks`, `/api/v1/checkins`)
* `GET /api/v1/tasks`: List current user's tasks.
* `POST /api/v1/tasks`: Create task (`name`, `category`, `planned_time`, `frequency`).
* `PUT /api/v1/tasks/{task_id}`: Update task (scoped to authenticated owner).
* `DELETE /api/v1/tasks/{task_id}`: Delete task (scoped to authenticated owner).
* `POST /api/v1/checkins`: Record checkin (`task_id`, `status`: `done` | `partial` | `missed`, `start_delay_minutes`, `duration_minutes`).

#### 6. Procrastination & Screen Usage (`/api/v1/procrastination`, `/api/v1/screen-usage`)
* `POST /api/v1/procrastination/start`: Trigger user-confirmed procrastination mode.
* `POST /api/v1/procrastination/{id}/end`: End procrastination episode with reflection notes.
* `POST /api/v1/screen-usage`: Ingest app usage session (`app_name`, `duration_seconds`).

#### 7. Micro-Experiments & AI Insights (`/api/v1/experiments`, `/api/v1/chat`)
* `POST /api/v1/experiments/suggest`: Generate personalized behavioral experiments based on detected friction.
* `POST /api/v1/experiments/{id}/evaluate`: Measure before vs. after behavioral outcome.
* `POST /api/v1/chat/explain`: AI explanation of behavioral patterns grounded strictly in deterministic backend evidence.

---

### D. Frontend Partner Integration Guide (React Native / Expo)

When connecting the React Native mobile frontend to FocusLoop backend:

1. **Token Storage:**
   Store `access_token` and `refresh_token` in secure device storage using `expo-secure-store`.
2. **API Requests:**
   Attach the access token on all API requests:
   ```typescript
   headers: {
     'Authorization': `Bearer ${accessToken}`,
     'Content-Type': 'application/json',
   }
   ```
3. **Silent Refresh Interceptor:**
   Use an Axios/Fetch response interceptor:
   * When receiving `401 Unauthorized` on an API call, pause outgoing requests.
   * Send `POST /api/v1/auth/refresh` with `{ refresh_token }`.
   * If successful, update the stored `access_token` and retry the original failed request.
   * If refresh fails (e.g. session expired or revoked), delete stored tokens and navigate to the Login screen.
4. **Logout Flow:**
   Call `POST /api/v1/auth/logout` with `{ refresh_token }`, clear local SecureStore, and redirect to the Welcome screen.

---

### E. Comprehensive Running & Testing Guide

#### 1. Backend Setup & Startup (FastAPI + PostgreSQL / SQLite)

1. **Activate Virtual Environment & Install Dependencies:**
   ```bash
   cd backend
   source ../.venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Migrations (Alembic):**
   ```bash
   alembic upgrade head
   ```

3. **Run Automated Test Suite:**
   ```bash
   pytest -v
   ```
   *36/36 tests passing: Covers JWT authentication, persistent sessions, PostgreSQL persistence, foreign-key cascades, deterministic behavior engine, privacy isolation, and grading strategies.*

4. **Start Local FastAPI Development Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   * **Base API URL:** `http://localhost:8000`
   * **Interactive Swagger Documentation:** `http://localhost:8000/docs`
   * **ReDoc Documentation:** `http://localhost:8000/redoc`

---

#### 2. Mobile Frontend Setup & Startup (React Native + Expo)

1. **Navigate & Install Frontend Dependencies:**
   ```bash
   cd mobile
   npm ci
   ```

2. **Start the Expo Development Server:**
   ```bash
   npx expo start
   ```
   *(Alternatively: `npm start`)*

3. **Opening the App on a Physical Android Phone via Expo Go:**
   * **Step 1:** Download and install the **Expo Go** app from the [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent).
   * **Step 2:** Ensure your computer and your Android phone are connected to the **same Wi-Fi network**.
   * **Step 3:** Open Expo Go on your phone, tap **"Scan QR code"**, and scan the QR code displayed in your terminal.
   * **Step 4 (Manual IP Alternative):** If scanning doesn't trigger automatically, tap **"Enter URL manually"** in Expo Go and enter the Metro URL shown in your terminal (e.g. `exp://192.168.1.XX:8081`).

4. **Network & Public Wi-Fi / Tunnel Mode:**
   If you are on a restricted network (such as university or office Wi-Fi, cellular hotspot, or firewall) that prevents direct local IP connections, use Expo's tunnel mode:
   ```bash
   npx expo start --tunnel
   ```
   *This generates a secure public tunnel via `@expo/ngrok` so you can test on any phone without local network restrictions.*

5. **Running on Other Targets:**
   * **Web Browser:** Press `w` in the terminal (opens `http://localhost:8081`).
   * **Android Emulator:** Press `a` in the terminal (requires Android SDK / Emulator).
   * **iOS Simulator:** Press `i` in the terminal (macOS with Xcode).

---

#### 3. Verifying the Full Stack

| Component | Verification Command | Expected Result |
|---|---|---|
| **Backend API** | `curl http://localhost:8000/api/v1/health` | `{"status":"ok",...}` |
| **Backend Tests** | `pytest -v` | `36 passed in ~1.5s` |
| **Frontend Modules** | `npx tsc --noEmit` | `0 errors (Clean exit code 0)` |
| **Expo Dev Server** | `npx expo config` | Valid app configuration JSON |

---

# 39. Development Progression Log

A chronological record of every implementation milestone completed on this project.

---

## Session 1 — Backend Foundation & Auth

### What was built

- **FastAPI project scaffolding** — `backend/` directory with `app/main.py`, `app/core/`, `app/models/`, `app/schemas/`, `app/api/` layout.
- **SQLAlchemy ORM + Alembic migrations** — Full 15-table schema including `users`, `tasks`, `task_checkins`, `procrastination_events`, `screen_usage`, `refresh_sessions`, `behavior_metrics`, `behavior_patterns`, `behavior_profiles`, `experiments`, `experiment_results`, `conversations`, `messages`, `friendships`.
- **SQLite development fallback / PostgreSQL primary** — Configurable via `DATABASE_URL` in `.env`.
- **Argon2id password hashing** (`argon2-cffi`) — No plaintext passwords stored or exposed.
- **JWT access tokens** (HMAC-SHA256 / HS256) — 60-minute expiry, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Persistent refresh sessions** — 256-bit cryptographically secure tokens stored as SHA-256 hashes in `refresh_sessions` table. 30-day validity.
- **Explicit server-side revocation** — `POST /api/v1/auth/logout` sets `revoked_at`, invalidating future refresh attempts.
- **Zero identity spoofing** — All protected endpoints resolve user identity strictly from the verified JWT payload `sub` field.
- **Cross-user isolation** — All resources (tasks, check-ins, procrastination events, screen usage) are strictly scoped to `current_user.id`. Unauthorized access returns `404`.

### Key files created

```text
backend/app/main.py
backend/app/core/database.py
backend/app/core/deps.py
backend/app/core/security.py
backend/app/models/user.py
backend/app/models/task.py
backend/app/models/checkin.py
backend/app/models/procrastination.py
backend/app/models/social.py
backend/app/api/auth.py
backend/app/api/users.py
backend/app/api/tasks.py
backend/app/api/checkins.py
backend/app/api/procrastination.py
backend/app/api/screen_usage.py
backend/alembic/
backend/requirements.txt
backend/.env.example
```

---

## Session 2 — Behavior Engine & Pattern Detection

### What was built

- **Deterministic Behavior Engine** (`backend/app/behavior/metrics.py`) — Zero LLM involvement:
  - `compute_completion_rate()` — Ratio of `done` check-ins across configurable time window.
  - `compute_average_start_delay()` — Mean start delay in minutes across recorded check-ins.
  - `compute_focus_ratio()` — Ratio of completed focus time to total planned time.
  - `compute_top_distractions()` — Ranked distraction apps from procrastination window screen usage.
  - `compute_time_of_day_performance()` — Completion and delay breakdown by Morning / Afternoon / Evening / Night windows.
  - `compute_behavior_progress_curve(days=14)` — Day-by-day behavioral trend with states: `improving`, `stable`, `setback`, `recovery`.

- **Statistical Pattern Detection Engine** (`backend/app/behavior/patterns.py`) — Detects:
  - `afternoon_focus_friction` — Elevated start delay for tasks planned 14:00–17:00.
  - `morning_clarity` — Significantly lower start delay for tasks planned 06:00–11:00.
  - `start_delay_resistance` — Global elevated procrastination pattern across all time windows.
  - Each pattern stores: `confidence` (`low` / `moderate` / `high`), `sample_size`, `supporting_metrics` (JSON), `status` (`active` / `improving` / `resolved`).

- **Behavior Profile Manager** (`backend/app/behavior/profile.py`):
  - `refresh_profile()` — Recalculates all metrics and patterns, writes to `behavior_profiles`.
  - `get_personal_profile()` — Full private profile for the authenticated owner.
  - `get_social_profile(viewer_id)` — Visibility-filtered social profile for friend-facing display.
  - `update_visibility(updates)` — Independent per-field privacy toggle.

- **Grading & Level System** (`backend/app/behavior/grading.py`):
  - 5-tier milestone progression: Foundation → Pattern Explorer → Momentum Builder → Habit Optimizer → Deep Focus Master.
  - Multi-dimensional score synthesis: 45% completion rate + 35% start delay performance + 20% distraction resistance.
  - `behavior_score`, `improvement_score`, `experiment_effectiveness`, `consistency` stored on `BehaviorProfile`.

### Key files created

```text
backend/app/behavior/metrics.py
backend/app/behavior/patterns.py
backend/app/behavior/profile.py
backend/app/behavior/grading.py
backend/app/api/behavior.py
backend/app/models/behavior.py
```

---

## Session 3 — Social Profile & Privacy System

### What was built

- **Dual-profile architecture:**
  - `GET /api/v1/profile/me` — Owner's complete personal profile (all private behavioral intelligence, all metrics, patterns, experiments, strengths, weaknesses, insights).
  - `GET /api/v1/profile/users/{user_id}` — Friend-facing social profile, strictly filtered by target user's visibility settings.

- **`DEFAULT_PROFILE_VISIBILITY`** defaults:

  | Field | Default |
  |---|---|
  | `current_level` | **Private** |
  | `behavior_score` | **Private** |
  | `behavioral_patterns` | **Private** |
  | `improvement_score` | Public |
  | `experiment_effectiveness` | Public |
  | `consistency` | Public |

- **Backend privacy enforcement** — When a field is private, its value is never read from the database. The key is absent from the `public_metrics` dict before Pydantic serialization. The Pydantic `SocialMetrics` schema fills absent keys with `null` (known nuance: value is withheld, wire format shows `null` rather than a fully omitted key).

- **Independent visibility toggles** — `PUT /api/v1/profile/visibility` or `PATCH /api/v1/profile/visibility` update individual fields without leaking others.

- **Friendship management** — `POST /api/v1/social/friends`, `DELETE /api/v1/social/friends/{id}`, `GET /api/v1/social/friends`, `GET /api/v1/social/friends/{id}/profile`.

- **Pydantic schemas** (`backend/app/schemas/profile.py`):
  - `PersonalProfileResponse` — Full internal profile with `UserIdentity`, `PersonalMetrics`, `ProfileVisibilitySettings`, `ProgressCurvePoint[]`, `behavioral_intelligence`.
  - `SocialProfileResponse` — Filtered social profile with `SocialMetrics` (all fields Optional).
  - `ProfileVisibilitySettings` / `ProfileVisibilityUpdate`.

### Key files created / updated

```text
backend/app/schemas/profile.py
backend/app/api/profile.py
backend/app/api/social.py
backend/app/models/social.py
backend/app/schemas/social.py
```

---

## Session 4 — AI Context Builder, LLM Integration & Chat

### What was built

- **`AIContext` Pydantic schema** (`backend/app/schemas/ai.py`) — Structured, type-safe container for grounded behavioral context passed to the LLM:
  - `user_context` — Non-identifying user context (timezone, account age).
  - `metrics_snapshot` — Current deterministic metrics (completion rate, start delay, focus ratio).
  - `active_patterns` — Detected behavioral patterns with confidence and sample size.
  - `recent_experiments` — Last 5 experiments with status and outcome.
  - `intent` — Request intent (`explain_pattern` / `suggest_experiment` / `general_chat` / `progress_check`).
  - `provenance` — Source attribution for each data field.

- **`AIContextBuilder`** (`backend/app/ai/context_builder.py`) — Intent-driven context builder:
  - Resolves current user metrics via `BehaviorMetricsCalculator`.
  - Loads active behavioral patterns.
  - Loads recent experiment history.
  - Filters context by intent — e.g., `explain_pattern` only injects pattern data; `suggest_experiment` only injects friction metrics and experiment history.
  - Tracks provenance for every field included in context.
  - Privacy-scoped: never injects friend-visible-only fields into chat context.

- **System prompt hardening** (`backend/app/ai/prompts.py`):
  - Strict grounding constraint: AI may only reference values present in the provided `AIContext`.
  - Non-judgmental tone: forbidden language list (lazy, bad, unfocused, distracted by choice).
  - Mandatory uncertainty signaling when sample size < 5.
  - Deterministic fallback instructions when no context data is available.

- **`LLMClient`** (`backend/app/ai/llm.py`) — Updated to:
  - Accept `AIContext` object rather than raw string.
  - Serialize context as structured JSON in the system prompt.
  - Use deterministic fallback response when LLM is unavailable or context is empty.
  - Log provenance for auditability.

- **Chat API** (`backend/app/api/chat.py`) — Updated:
  - `POST /api/v1/chat/explain` — Builds `AIContext` with `intent=explain_pattern`, calls LLM, returns grounded explanation.
  - `POST /api/v1/chat/message` — Builds `AIContext` with intent inferred from message content, maintains conversation history in `messages` table.

- **Integration tests** (`backend/tests/test_ai_context_builder.py`):
  - 8 additional tests covering: empty context fallback, intent-based filtering, provenance tracking, privacy scoping, and chat end-to-end flow.
  - Total test suite: **46 tests — 46/46 passing**.

### Key files created / updated

```text
backend/app/schemas/ai.py         (Created)
backend/app/ai/context_builder.py (Updated)
backend/app/ai/prompts.py         (Updated)
backend/app/ai/llm.py             (Updated)
backend/app/api/chat.py           (Updated)
backend/tests/test_ai_context_builder.py (Created)
```

---

## Session 5 — React Native Frontend Audit & Demo Data Removal

### What was audited (read-only)

Complete audit of `mobile/src/` identified all hardcoded/demo data:
- Fake user names and profile information.
- Hardcoded task counts and completion values.
- Static focus hours and start-delay data.
- Demo experiment results and fake AI conversations.
- Placeholder behavioral insights and fake pattern descriptions.
- Demo grades, points, mastery systems, and leaderboard data.
- Fake authentication flows (skip-login, demo user bypass).

### What was removed

All hardcoded product/behavioral data was replaced with proper loading / empty states:
- `useAuth` hook cleared of fake user object; replaced with `null` initial state and real token checks.
- All screen components replaced static metrics arrays with empty arrays / `null` while data loads.
- Fake AI conversation pre-population removed from chat state initialization.
- Demo task lists replaced with empty arrays; loading skeletons shown until real data arrives.
- Fake experiment results removed; `experiments` state initialized as `[]`.
- Leaderboard, gamification points, and fake ranking data removed entirely.
- Onboarding demo-skip path removed; all auth flows now require real backend registration/login.

---

## Session 6 — Frontend ↔ Backend Integration (Task 5)

### What was built

Full React Native → FastAPI integration across all major feature areas:

#### Authentication
- `authService.ts` — `register()`, `login()`, `logout()`, `refreshToken()` calling real auth endpoints.
- `useAuth.ts` hook — Reads/writes tokens via `expo-secure-store`; implements silent refresh interceptor on 401 responses.
- Axios instance with request interceptor injecting `Authorization: Bearer` header.

#### Tasks & Check-ins
- `taskService.ts` — `getTasks()`, `createTask()`, `updateTask()`, `deleteTask()`.
- `checkinService.ts` — `createCheckin()`, `getCheckins()`.
- `useTasks.ts` hook connecting Today screen to real task list.

#### Behavior & Profile
- `behaviorService.ts` — `getSummary()`, `getPatterns()`, `getProfile()`, `refresh()`.
- `profileService.ts` — `getMyProfile()`, `getVisibility()`, `updateVisibility()`, `getProgressCurve()`.
- Insights screen connected to `GET /api/v1/behavior/summary` and `GET /api/v1/profile/me`.

#### Procrastination
- `procrastinationService.ts` — `startSession()`, `endSession()`, `getEvents()`.
- Delay Log screen connected to real procrastination session management.

#### Experiments
- `experimentService.ts` — `suggest()`, `getExperiments()`, `evaluateExperiment()`.
- Experiments screen connected to real suggest and evaluate endpoints.

#### AI Chat
- `chatService.ts` — `sendMessage()`, `getConversations()`, `getMessages()`.
- AI Coach screen connected to `POST /api/v1/chat/message` and `POST /api/v1/chat/explain`.

#### Social / Friends
- `socialService.ts` — `getFriends()`, `addFriend()`, `removeFriend()`, `getFriendProfile()`.
- `GET /api/v1/profile/users/{id}` used to load friend social profiles with backend-enforced privacy filtering.

---

## Session 7 — My Profile Screen & Logout Architecture (Task 6)

### What was built

- **`MyProfileScreen`** — New dedicated screen accessible from the top-right avatar control in all tabs:
  - Displays authenticated user's name, username, bio, avatar, and account details from `GET /api/v1/profile/me`.
  - Shows private behavioral metrics (behavior score, current level, consistency, improvement score, experiment effectiveness) — visible only to the owner.
  - **Privacy controls panel** — Toggle switches for each visibility setting, calling `PATCH /api/v1/profile/visibility` on change.
  - **Logout button** — Moved from Insights screen to My Profile screen. Calls `POST /api/v1/auth/logout`, clears `expo-secure-store` tokens, and navigates to Welcome screen.

- **Separation of profile concepts:**
  - `MyProfileScreen` — Private, owner-only view of full behavioral intelligence and account settings.
  - `FriendProfileScreen` (existing, unchanged) — Public friend-facing view using `SocialProfileResponse`; visibility-filtered by backend.

- **Top-right avatar control** — Added to all tab navigator headers; navigates to `MyProfileScreen`.

---

## Session 8 — Check-in History & Procrastination Event UI (Task 7)

### What was built

#### Check-in History
- `useCheckins.ts` hook calling `checkinService.getCheckins()` (`GET /api/v1/checkins`).
- Check-in history section added to the Today / Home screen:
  - Groups check-ins by date.
  - Displays task name, completion status badge (`done` / `partial` / `missed`), start delay, and duration.
  - Empty state when no check-ins exist.
  - Loading skeleton during fetch.

#### Procrastination Event History
- `useProcrastination.ts` hook calling `procrastinationService.getEvents()` (`GET /api/v1/procrastination`).
- Delay Log screen updated to display event history:
  - Each event shows start time, end time, duration, and user-provided reflection notes.
  - Active session (no `ended_at`) clearly indicated with a pulsing indicator.
  - Empty state when no events exist.

---

## Session 9 — AI Context Builder Hardening (Task 8)

### What was built

Extended and hardened the existing AI context infrastructure:

- **`AIContext` schema extended** (`backend/app/schemas/ai.py`):
  - Added `data_quality` field: `sufficient` / `insufficient` / `no_data`.
  - Added `window_days` provenance tracking.
  - Added `experiment_count` and `pattern_count` to context metadata.

- **`AIContextBuilder` strengthened** (`backend/app/ai/context_builder.py`):
  - Added minimum data threshold checks — returns `data_quality: insufficient` rather than hallucinating from sparse data.
  - Added explicit `sample_size` and `window_days` injection for every metric included in context.
  - Added experiment outcome injection with before/after metric values from `experiment_results` table.
  - Privacy scoping verified: builder never accesses other users' profiles.

- **Prompt system hardened** (`backend/app/ai/prompts.py`):
  - Added explicit `INSUFFICIENT_DATA` response template used when `data_quality != sufficient`.
  - Added provenance citation requirement: AI must reference specific metric values present in context.
  - Added forbidden pattern list: no invented numbers, no causal claims without experiment evidence.

- **Integration tests extended** (`backend/tests/test_ai_context_builder.py`):
  - Added tests for insufficient data handling.
  - Added tests for experiment outcome injection.
  - Added tests for cross-user privacy isolation.
  - **Total: 46/46 tests passing.**

---

## Session 10 — Privacy Verification Audit (Read-Only)

### What was verified

Complete read-only audit of friend-facing profile privacy enforcement:

#### Findings

1. **Business logic correctly withholds private data** — In `BehaviorProfileManager.get_social_profile()`, when a visibility flag is `False`, the field's value is never read from `profile_obj`. The key is entirely absent from `public_metrics` before serialization.

2. **Wire format shows `null` for private fields (known nuance)** — The `SocialMetrics` Pydantic schema declares all fields as `Optional[float] = None`. When a key is absent from the source dict, Pydantic fills it with `null` in the serialized JSON. The actual behavioral value is never leaked, but the field name is present with `null` instead of being fully omitted.

3. **Default visibility is correctly private for sensitive fields:**

   | Field | Default | Value leaked to friend? |
   |---|---|---|
   | `behavior_score` | Private | ❌ Never |
   | `current_level` | Private | ❌ Never |
   | `behavioral_patterns` | Private | ❌ Never |
   | `improvement_score` | Public | ✅ Shared |
   | `experiment_effectiveness` | Public | ✅ Shared |
   | `consistency` | Public | ✅ Shared |

4. **Friendship check is enforced in `get_social_profile()`** — The method checks `Friendship.status == "accepted"` before returning data.

5. **Both social endpoints use the same privacy path** — `GET /api/v1/profile/users/{id}` (profile router) and `GET /api/v1/social/friends/{id}/profile` (social router) both call `BehaviorProfileManager.get_social_profile(viewer_id=current_user.id)` — no bypass path exists.

#### Known issue identified (not yet fixed)
The `SocialMetrics` Pydantic schema does not use `model_config = ConfigDict(exclude_none=True)`, so private fields appear as `"behavior_score": null` in the wire response instead of being fully omitted. The actual numeric value is not leaked. Fix deferred to a future task.

---

## Session 11 — Android-to-Mac Backend Connectivity Fix

### What was built

Physical Android device (via Expo Go) was resolving the API base URL to `localhost` instead of the Mac's LAN IP address, making all API calls fail silently.

- **Root cause identified** — `mobile/src/services/api.ts` was using `process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'`. On a physical Android device, `localhost` is the device itself, not the development machine.
- **`.env` file created** in `mobile/` — Added `EXPO_PUBLIC_API_URL=http://10.167.116.107:8000` so the Expo environment variable system resolves the correct LAN IP at build time rather than falling back to `localhost`.
- **`mobile/.env.example` updated** — Documents `EXPO_PUBLIC_API_URL` as a required developer environment variable with instructions for setting the correct IP.
- **`mobile/app.json` / `expo.extra` not modified** — The fix was intentionally applied only to the environment layer; the centralized `api.ts` architecture was preserved unchanged.
- **End-to-end verified** — All API calls (auth, tasks, check-ins, behavior, chat) confirmed working on the physical Android phone via Expo Go.

### Key files created / updated

```text
mobile/.env                  (Created — local only, gitignored)
mobile/.env.example          (Updated — documents EXPO_PUBLIC_API_URL)
```

---

## Session 12 — Username-Based Friend Requests with Accept/Decline Flow

### What was built

Replaced the brittle "Enter Friend's UUID" UX with a proper social graph flow based on `@username` lookup, pending states, and explicit accept/decline actions.

#### Backend

- **`GET /api/v1/social/users/search?username=@handle`** — New endpoint: case-insensitive username lookup returning public identity (`id`, `username`, `display_name`). Returns `404` if user not found, `400` if searching for yourself.
- **`POST /api/v1/social/friends/request`** — Sends a friend request (`{ "username": "@handle" }`) creating a `Friendship` row with `status = "pending"`. Idempotent: re-sending a pending request returns `200` rather than creating a duplicate.
- **`POST /api/v1/social/friends/{friendship_id}/accept`** — Authenticated recipient sets `status = "accepted"`. Returns `403` if called by the requester.
- **`POST /api/v1/social/friends/{friendship_id}/decline`** — Authenticated recipient deletes the pending `Friendship` row. Returns `403` if called by the requester.
- **`GET /api/v1/social/friends/requests/incoming`** — Lists all pending requests where `friend_id = current_user.id`.
- **`GET /api/v1/social/friends/requests/outgoing`** — Lists all pending requests sent by the current user.
- **Friendship status normalization** — All existing `Friendship` rows without a `status` value were defaulted to `"accepted"` during migration.
- **Alembic migration `0002_friendship_status_and_pending`** — Added `status` column to `friendships` table with default `"accepted"` and indexed for query performance.

#### Frontend

- **Add Friend modal rebuilt** — New flow: text input for `@username` → search button → user card preview → "Send Request" button.
- **`useSocial()` hook extended** — Added `searchUser()`, `sendRequest()`, `acceptRequest()`, `declineRequest()`, `incomingRequests`, `outgoingRequests` state.
- **`socialService.ts` extended** — New methods wiring all six new endpoints.
- **Pending requests inbox** — New section in Friends screen showing incoming requests with Accept / Decline actions.
- **Outgoing requests section** — Shows sent requests with pending badge and cancel option.
- **Friend list unchanged** — Existing confirmed-friend display preserved.

### Key files created / updated

```text
backend/alembic/versions/0002_friendship_status_and_pending.py  (Created)
backend/app/api/social.py           (Updated — 6 new endpoints)
backend/app/schemas/social.py       (Updated — new request/response schemas)
mobile/src/services/socialService.ts (Updated)
mobile/src/hooks/useSocial.ts       (Updated)
mobile/src/app/(tabs)/social.tsx    (Updated — new Add Friend + inbox UI)
```

---

## Session 13 — Personalized Onboarding, Structured User Context & AI Coach Integration

### What was built

Full onboarding pipeline feeding structured per-user context into the AI Coach system, removing all generic AI responses.

#### Onboarding Flow (5-Step Mobile)

- **Step 1 — Welcome:** Brand splash with product value proposition.
- **Step 2 — Goal:** Single primary goal selection (`study_consistently`, `build_exercise_habit`, `improve_focus`, `reduce_procrastination`, `custom`).
- **Step 3 — Role:** Self-description (`student`, `professional`, `freelancer`, `other`) for contextualization.
- **Step 4 — Focus Challenges:** Multi-select from common friction types (`starting_tasks`, `staying_focused`, `phone_distraction`, `procrastination`, `time_management`).
- **Step 5 — Schedule:** Preferred active hours (`morning`, `afternoon`, `evening`, `night`) and typical day structure.
- **Completion:** Calls `POST /api/v1/onboarding` — saves context, marks user as onboarded, redirects to main app.

#### Backend: `UserContext` Model & API

- **`UserContext` SQLAlchemy model** (`backend/app/models/user_context.py`):
  - `user_id` (FK to `users`), `goal`, `role`, `focus_challenges` (JSON array), `preferred_schedule` (JSON object), `onboarding_completed` (bool), `created_at`, `updated_at`.
- **`POST /api/v1/onboarding`** — Creates or updates `UserContext` for the authenticated user.
- **`GET /api/v1/onboarding/status`** — Returns whether the user has completed onboarding and their current context.
- **Alembic migration `0003` (pre-lifecycle)** — Added `user_context` table.

#### AI Coach Context Integration

- **`AIContextBuilder` updated** — Now loads `UserContext` before building context for any chat request:
  - Injects `goal`, `role`, `focus_challenges`, and `preferred_schedule` into the system prompt.
  - AI Coach references the user's goal and challenges in every response rather than providing generic advice.
- **System prompt updated** — Added persona-aware coaching instructions: the AI references the user's stated challenges and goal explicitly.
- **`data_quality` gating** — If onboarding is incomplete, AI Coach prompts the user to finish onboarding before providing personalized advice.

#### Frontend Integration

- **`OnboardingScreen` (5 screens)** — Created at `mobile/src/app/onboarding/`.
- **`onboardingService.ts`** — `submitOnboarding()`, `getOnboardingStatus()`.
- **Auth flow updated** — After successful registration, checks `GET /api/v1/onboarding/status`; redirects to onboarding if incomplete, else to main app.
- **`useOnboarding()` hook** — Manages onboarding state, submission, and navigation.

### Key files created / updated

```text
backend/app/models/user_context.py          (Created)
backend/app/schemas/user_context.py         (Created)
backend/app/api/onboarding.py               (Created)
backend/app/ai/context_builder.py           (Updated — UserContext injection)
backend/app/ai/prompts.py                   (Updated — persona-aware prompts)
backend/alembic/versions/0003_user_context.py (Created)
mobile/src/app/onboarding/                  (Created — 5-screen flow)
mobile/src/services/onboardingService.ts    (Created)
mobile/src/hooks/useOnboarding.ts           (Created)
```

---

## Session 14 — Task Lifecycle: One-Time vs Daily Recurring Tasks & Idempotent Check-ins

### What was built

Corrected the fundamental task/check-in data model to properly represent task recurrence and per-day occurrences, eliminating the conceptual mismatch between one-time tasks and daily habits.

#### Core Conceptual Change

Previously the system had no distinction between tasks that should happen once and tasks that repeat daily. This caused:
- One-time tasks reappearing after completion.
- Duplicate check-in rows when the same status was re-submitted.
- Today screen unable to correctly determine a task's status for the current day.

#### Backend Changes

- **`Task.frequency` normalized** — Values are now strictly `'once'` or `'daily'`. All existing rows with legacy values (`'one_time'`, `'One Time'`, etc.) were normalized via Alembic data migration.
- **`TaskCheckin` `UniqueConstraint`** — Added `UniqueConstraint('task_id', 'date', name='uq_task_checkin_date')` enforced at both the database level (Postgres/SQLite) and the SQLAlchemy model level. Historical duplicate rows were deduplicated before the constraint was applied.
- **`POST /api/v1/checkins` — Idempotent upsert:**
  - If a check-in for `(task_id, date)` does not exist → creates new row (HTTP 201).
  - If a check-in for `(task_id, date)` already exists → updates `status`, `duration_minutes`, `completed_at` in-place (HTTP 200).
  - No duplicate rows are ever created; retrying the same status is safe.
- **`GET /api/v1/tasks` — Occurrence-aware response enrichment:**
  - Each task object now includes `today_status`: the check-in status for today (`'done'` / `'partial'` / `'missed'` / `null` if not yet checked in).
  - One-time tasks with `status = 'done'` on a **prior** date are excluded from the active task list (they are complete; no future occurrence expected).
  - One-time tasks with `status = 'done'` on **today** are included with `today_status = 'done'`.
  - Daily tasks always appear; their `today_status` reflects today's check-in.
- **Alembic migration `0003_task_lifecycle_and_checkin_unique`** — Applied in order:
  1. Added `UniqueConstraint` to `task_checkins`.
  2. Deduplicated existing check-in rows (keeping the most recent per `(task_id, date)`).
  3. Normalized `Task.frequency` values to `'once'` / `'daily'`.
- **Tests — `backend/tests/test_task_lifecycle.py`** — New lifecycle-specific test file:
  - One-time task completed on prior date excluded from active list.
  - One-time task completed today still included.
  - Daily task always included regardless of past check-ins.
  - Duplicate check-in returns 200 and updates in-place (no new row).
  - `today_status` reflects correct value per scenario.
  - All backend tests passing.

#### Frontend Changes

- **`TaskFrequency` TypeScript type** — Added to `mobile/src/types/tasks.ts`:
  ```typescript
  export type TaskFrequency = 'once' | 'daily';
  ```
- **Task card rendering updated** — `mobile/src/app/(tabs)/index.tsx`:
  - Action buttons (Done / Partial / Missed) are only rendered if `today_status` is `null`.
  - If `today_status === 'done'`: renders `✓ Completed` badge.
  - If `today_status === 'partial'`: renders `◐ Partial` badge.
  - If `today_status === 'missed'`: renders `× Missed` badge.
  - This eliminates ghost re-submission UX.
- **New Task modal updated** — Frequency selector added: `'Once'` / `'Every day'` toggle replaces the former free-text field. Defaults to `'daily'`.
- **`useTasks` hook hardened** — Added in-flight request locking: a second tap on a check-in button while the first request is in-flight is silently dropped. State is resynchronized from the server response after each successful check-in.
- **TypeScript compilation verified** — `npx tsc --noEmit` passes with zero errors.
- **Expo export verified** — `npx expo export --platform web` completes successfully (build integrity check).

### Key files created / updated

```text
backend/alembic/versions/0003_task_lifecycle_and_checkin_unique.py  (Created)
backend/app/models/checkin.py          (Updated — UniqueConstraint added)
backend/app/schemas/task.py            (Updated — frequency validation)
backend/app/schemas/checkin.py         (Updated — date format validation)
backend/app/api/checkins.py            (Updated — idempotent upsert logic)
backend/app/api/tasks.py               (Updated — today_status enrichment)
backend/tests/test_task_lifecycle.py   (Created — lifecycle-specific tests)
mobile/src/types/tasks.ts              (Updated — TaskFrequency type)
mobile/src/hooks/useTasks.ts           (Updated — in-flight locking, state sync)
mobile/src/app/(tabs)/index.tsx        (Updated — occurrence-aware UI)
```

---

### Milestone: Behavioral Data Integrity, Metric Correlation & No-Data Semantics

To establish a truthful closed-loop behavioral system (Goal → Task → Collect Evidence → Measure → Understand Pattern → AI Explanation → Personalized Experiment → Measure Result → Learn → Next Action), the metric pipeline and UI data flows were audited and corrected:

#### 1. Metric Scale Integrity & Unit Separation
- **`completion_rate`**: Standardized strictly as a **0.0 – 1.0 ratio** (rendered via `formatRatioToPercent(val)` → e.g. `0.75` → `75%`).
- **`consistency`, `improvement_score`, `experiment_effectiveness`, `behavior_score`**: Standardized strictly as **0.0 – 100.0 scores** (rendered via `formatScore(val)` / `formatScorePercent(val)` → e.g. `50.0` → `50%`, eliminating historical `5000%` and `7500%` bugs caused by rogue `* 100` multipliers in mobile views).

#### 2. Truthful "No Data" vs "Zero" Semantics
- `average_start_delay_minutes` in schemas and calculation engines is now `Optional[float] = None`.
- If no start delays were recorded/observed, it returns `None` (rendered in UI as `"—"` and `"• No delay logged today"`).
- If the user explicitly started on time with zero delay, it returns `0.0` (rendered in UI as `"0 mins"` and `"• On time today"`).
- `compute_behavior_score` safely handles `None` start delay using a neutral 70.0 promptness factor without skewing the composite behavior score.

#### 3. Date Scoping & Isolated Daily Summaries
- `GET /api/v1/behavior/summary?date=YYYY-MM-DD` now strictly isolates statistics to the requested date (occurrences, delays, and distraction events).
- Omitting `date` preserves lifetime aggregate calculation.
- Today tab specifically requests `date=getLocalDateString()` (local calendar `YYYY-MM-DD`), preventing UTC date-boundary shifts and cross-day leakage.

#### 4. Evidence-Backed Progress Curve
- `compute_behavior_progress_curve` strictly returns evidence-backed data points.
- New users with 0 check-ins receive `[]` (empty list), allowing the UI to render an honest "Need at least 2 days of check-ins to plot your curve" empty state instead of a fabricated 14-day flat line at 50.0 with `trend='stable'`.
- The first real evidence point is labeled `trend='initial'`. Trends (`improving`, `setback`, `recovery`, `stable`) only calculate between consecutive days with actual recorded evidence.

#### 5. Real-Time Cross-Tab State Synchronization
- Replaced decoupled stale React hook state with React Native `DeviceEventEmitter` broadcasting `focusloop:checkin_recorded`.
- When any check-in completes in `useTasks`, `useBehavior` and `useProfile` instantly re-fetch today's summary, behavior metrics, and progress curve without requiring a manual pull-to-refresh.

### Key files created / updated for Data Integrity

```text
backend/app/schemas/behavior.py             (Updated — average_start_delay_minutes Optional[float], date param)
backend/app/behavior/metrics.py             (Updated — date-scoped filters, truthful start delay, evidence-backed curve)
backend/app/api/behavior.py                 (Updated — date query parameter on /summary)
backend/tests/test_data_integrity_and_metrics.py (Created — 5 new regression tests verifying metric isolation & contract)
mobile/src/utils/formatters.ts              (Created — getLocalDateString, formatRatioToPercent, formatScorePercent)
mobile/src/types/behavior.ts                (Updated — scale annotations, nullable delay, initial trend)
mobile/src/types/profile.ts                 (Updated — scale annotations, nullable delay)
mobile/src/services/behavior.ts             (Updated — date query forwarding)
mobile/src/hooks/useBehavior.ts             (Updated — date param, DeviceEventEmitter auto-refresh)
mobile/src/hooks/useProfile.ts              (Updated — DeviceEventEmitter auto-refresh)
mobile/src/hooks/useTasks.ts                (Updated — emit focusloop:checkin_recorded, getLocalDateString)
mobile/src/app/(tabs)/index.tsx             (Updated — date-scoped summary, removed length fallback, null delay handling)
mobile/src/app/(tabs)/insights.tsx          (Updated — removed *100 scale bugs, initial trend badge)
mobile/src/app/profile.tsx                  (Updated — removed *100 scale bugs on consistency & experiments)
```

---

## Session 15 — Phase 1: Time-Bounded Experiment Metrics & Trustworthy Evaluation

### What was built

Corrected the fundamental flaw in experiment evaluation: the system was using **lifetime behavioral metrics** to evaluate short-duration experiments, allowing months of prior history to dilute the measured result, making experiment conclusions unreliable.

#### Core Problem Fixed

Before this change, `ExperimentEvaluator.evaluate_experiment()` called the global `compute_completion_rate()` and `compute_average_start_delay()` with no date boundaries. A 3-day experiment could be measured against 90 days of accumulated data, producing a baseline and result that were mathematically meaningless for the specific intervention window.

#### Time-Bounded Measurement Architecture

The evaluation logic was fully replaced with a two-window, non-overlapping measurement model:

```text
Baseline Window:   [start_date − 7 days,  start_date − 1 day]
Experiment Window: [start_date,            end_date           ]
```

- **`DEFAULT_EXPERIMENT_BASELINE_DAYS = 7`** — Fixed 7-day pre-experiment window. The baseline captures behavioral state immediately before the intervention, never overlapping the intervention period.
- **`MIN_EXPERIMENT_OBSERVATIONS = 3`** — Minimum check-in observations required in *both* windows to declare a conclusion. If either window has fewer than 3 observations, result is `"inconclusive"` with an explicit reason string in `result_summary`.

#### New Backend Methods (`backend/app/behavior/metrics.py`)

Two new time-scoped calculation methods were added to `BehaviorMetricsCalculator`:

- **`compute_start_delay_stats(start_date, end_date)`** — Returns `average_start_delay_minutes` and `sample_size` strictly bounded to `[start_date, end_date]`. Returns `None` for delay if zero check-ins have a recorded delay (semantically distinct from `0.0`).
- **`compute_task_completion_stats(start_date, end_date)`** — Returns `completion_rate` (0.0–1.0 ratio) and `sample_size` strictly bounded to `[start_date, end_date]`.

#### Inconclusive vs. Conclusive Semantics

| Condition | `conclusion` | `before_value` / `after_value` |
|:---|:---:|:---:|
| Either window < 3 observations | `"inconclusive"` | Preserved as-is (may be `None`) |
| No check-ins in experiment window | `"inconclusive"` | `after_value = None` |
| Zero baseline (division undefined) | Directional result | `percent_change = None` |
| ≥ 3 observations on both sides | `"positive"` / `"neutral"` / `"negative"` | Calculated values |

The `result_summary` string always includes a disclaimer: *"does not prove causality"*.

#### Experiment Lifecycle Enforcement

`ExperimentEvaluator.evaluate_experiment()` now enforces a hard lifecycle gate:
- Only experiments with `status == "active"` can be evaluated.
- `status == "suggested"` or `status == "completed"` returns `None` and the API layer raises `HTTP 400` with a clear reason.
- After successful evaluation, `exp.status` is set to `"completed"` atomically with the `ExperimentResult` commit.
- `BehaviorProfileManager.refresh_profile()` is called post-commit to incorporate the learned experiment outcome into the user's profile.

#### API Experiment Lifecycle (`PATCH /api/v1/experiments/{id}`)

New `PATCH` endpoint added to expose status transitions to the frontend:
- Accepts `{ "status": "active" | "dismissed" }` for the `suggested → active` and `suggested → dismissed` transitions.
- Ownership-enforced: only the experiment owner can update.
- Frontend uses this to implement the "Start Protocol" flow: `suggested` → user taps Start → `PATCH` sets `status = "active"` → experiment is live.

#### `ExperimentResponse` Schema (`backend/app/schemas/experiment.py`)

Schema aligned with what the frontend actually needs:
- `intervention_type`: `str` — Type of intervention (e.g., `"initiation_barrier"`, `"circadian_shift"`).
- `target_value`: `Optional[float]` — Numeric improvement target.
- `baseline_value`: `Optional[float]` — Baseline at experiment creation time.
- `target_metric`: `str` — Metric name (`"average_start_delay_minutes"` or `"completion_rate"`).
- `results`: `List[ExperimentResultResponse]` — Nested evaluation results (eager-loaded).
- `status`: `str` — Required, always present: `"suggested"` / `"active"` / `"completed"` / `"dismissed"`.

#### `ExperimentResultResponse` Schema

New schema with full evaluation output:
- `before_value`, `after_value`, `change_value` — Numeric windows comparison.
- `percent_change` — Optional (None when baseline is zero).
- `conclusion` — `"positive"` / `"neutral"` / `"negative"` / `"inconclusive"`.
- `result_summary` — Human-readable explanation string.

#### Automated Tests (`backend/tests/test_time_bounded_experiment_evaluation.py`)

11 regression tests added covering:

1. Pre-experiment baseline only (excludes experiment period data).
2. Experiment window only (excludes pre-experiment and post-experiment data).
3. No data during experiment window → `after_value = None`, `conclusion = "inconclusive"`.
4. Zero actual delay (`0.0` average) vs. no data (`None`) — semantically distinct.
5. Old historical data does not dilute result.
6. Boundary precision: `start − 7`, `start − 1`, `start`, `end`, `end + 1`.
7. Insufficient sample size (< `MIN_EXPERIMENT_OBSERVATIONS`) → `"inconclusive"`.
8. Directionality: lower is better (start delay metric).
9. Directionality: higher is better (completion rate metric).
10. Zero baseline safety: no division-by-zero, no NaN.
11. Status gate: `suggested` and `completed` experiments cannot be evaluated.

### Key files created / updated

```text
backend/app/experiments/evaluator.py                   (Rewritten — time-bounded, status-gated)
backend/app/behavior/metrics.py                        (Updated — compute_start_delay_stats, compute_task_completion_stats)
backend/app/schemas/experiment.py                      (Updated — ExperimentResponse, ExperimentResultResponse)
backend/app/api/experiments.py                         (Updated — PATCH status endpoint, lifecycle guard on evaluate)
backend/tests/test_time_bounded_experiment_evaluation.py (Created — 11 regression tests)
```

---

## Session 16 — Lab Screen Crash Fix & Experiment Status Lifecycle

### What was built

Fixed a reproducible `TypeError: Cannot read property 'toUpperCase' of undefined` crash on the Lab Screen (the `lab.tsx` tab, styled as the experiment management interface).

#### Root Cause

The crash occurred at:

```tsx
// BEFORE (crashing):
`Status: ${activeExperiment.status.toUpperCase()}`
```

The `status` field was not present on every `ExperimentResponse` returned by the backend. The backend schema had `status` as an optional field and older database rows (created before the lifecycle migration) did not have a `status` value populated. When `activeExperiment.status` was `undefined`, calling `.toUpperCase()` on it threw a `TypeError` and crashed the React Native render cycle.

The secondary contributing factor was that the `/suggest` endpoint returned a list, but the frontend `suggestExperiment()` function was mismatching the response type — the `useExperiments` hook was appending the returned array as a nested element rather than merging the new items, causing index-based lookups to produce unexpected objects.

#### Fixes Applied

**Backend — Schema Enforcement:**
- `status` field on `ExperimentResponse` marked as `str` (non-optional) with a default value of `"suggested"`. The SQLAlchemy model already had `default="suggested"` on the column; the schema now enforces this at the API boundary so `null` can never reach the frontend.

**Frontend — Null-safe status render (`mobile/src/app/(tabs)/lab.tsx`):**
- Status display uses a nullish fallback: `(activeExperiment.status || 'active').toUpperCase()`.
- Status pill in the experiment card list uses: `(exp.status || 'unknown').toUpperCase()`.
- This prevents any future `undefined`/`null` status value from crashing the render cycle.

**Frontend — `suggestExperiment()` return type fix (`mobile/src/hooks/useExperiments.ts`):**
- The hook now correctly handles the `POST /suggest` returning `ExperimentResponse[]`.
- After suggest, `refreshExperiments()` is called to re-fetch the full list rather than attempting to merge a partial response — this ensures the list state is always derived from a single authoritative server GET.
- The `handleSuggest()` callback now shows the most recently created experiment's title in the confirmation alert, or a generic success message if no title is available.

**Frontend — `startExperiment()` fix (`mobile/src/hooks/useExperiments.ts`):**
- `PATCH /api/v1/experiments/{id}` called with `{ status: "active" }` to transition from `suggested` to `active`.
- On success, `refreshExperiments()` called to synchronize list state.

**Frontend — TypeScript type alignment (`mobile/src/types/experiments.ts`):**
- `ExperimentResponse.status` typed as `string` (non-optional).
- `ExperimentResultResponse` schema defined with all evaluator output fields: `before_value`, `after_value`, `change_value`, `percent_change`, `conclusion`, `result_summary`.

#### Experiment Lifecycle UI

The Lab screen correctly handles all three experiment lifecycle states:

| Experiment `status` | UI State |
|:---|:---|
| `"suggested"` | "Start Protocol" button shown in card |
| `"active"` | Hero banner shows active experiment; "Evaluate Protocol Outcome" button rendered |
| `"completed"` | Results snippet shown in card with conclusion and change value |

No active experiment → hero banner shows "No Active Experiment" state with "Suggest Behavioral Protocol" button.

### Key files updated

```text
backend/app/schemas/experiment.py          (Updated — status non-optional, result schema fields)
mobile/src/app/(tabs)/lab.tsx              (Updated — null-safe status, status-aware UI, evaluation result display)
mobile/src/hooks/useExperiments.ts         (Updated — suggest/start/evaluate/refresh flow)
mobile/src/types/experiments.ts            (Updated — ExperimentResponse, ExperimentResultResponse type alignment)
```

---

## Current Implementation Status

| Component | Status | Notes |
|---|---|---|
| FastAPI Backend | ✅ Complete | Schema, Alembic migrations (×4), SQLite/PostgreSQL |
| Authentication & Persistent Sessions | ✅ Complete | Argon2id, JWT, SHA-256 refresh tokens, server-side revocation |
| Behavior Engine (Deterministic) | ✅ Complete | Completion rate, start delay, focus ratio, distraction ranking |
| Pattern Detection Engine | ✅ Complete | Statistical afternoon/morning/delay patterns with confidence |
| Behavior Profile & Intelligence | ✅ Complete | Personal full profile + social privacy-filtered profile |
| Social Profile & Privacy System | ✅ Complete | Dual-profile architecture, independent visibility toggles |
| Grading & Level Abstraction | ✅ Complete | 5-tier milestone system, multi-dimensional scoring |
| Username-Based Friend Requests | ✅ Complete | `@username` search → pending → accept/decline flow |
| AI Context Builder | ✅ Complete | Intent-based, grounded, provenance-tracked, privacy-scoped |
| AI Chat & Explain Endpoints | ✅ Complete | Grounded LLM calls, UserContext-personalized, deterministic fallback |
| Personalized Onboarding | ✅ Complete | 5-step flow: goal, role, challenges, schedule → `UserContext` |
| Structured User Context | ✅ Complete | `user_context` table feeding AI Coach personalization |
| Task Lifecycle (One-Time vs Daily) | ✅ Complete | `frequency: 'once' \| 'daily'`, per-day occurrence model |
| Task Check-in Idempotency | ✅ Complete | `UniqueConstraint(task_id, date)` + upsert in `POST /checkins` |
| `today_status` Occurrence Enrichment | ✅ Complete | `GET /tasks` returns current-day check-in status per task |
| Data Integrity & Metric Correlation | ✅ Complete | Strict scale alignment (0-1 vs 0-100), truthful `null` vs `0.0` start delay, isolated date-scoped summary |
| Truthful Progress Curve | ✅ Complete | Evidence-backed points only; no fabricated 14-day history for new users |
| Real-Time Cross-Tab State Sync | ✅ Complete | `DeviceEventEmitter` (`focusloop:checkin_recorded`) auto-syncs Today, Insights, Profile |
| **Time-Bounded Experiment Evaluation** | ✅ Complete | Pre-experiment baseline window vs. experiment window; `inconclusive` on sparse data; no lifetime dilution |
| **Experiment Lifecycle Enforcement** | ✅ Complete | `suggested → active → completed`; only `active` experiments can be evaluated |
| **Experiment Generator** | ✅ Complete | Pattern-driven suggestions (5-Minute Gateway, Morning Focus Alignment); idempotent (no duplicate titles) |
| **Lab Screen (Experiment UI)** | ✅ Complete | Crash fixed; status-aware hero banner, Start/Evaluate/Results display |
| **`ExperimentResultResponse` Schema** | ✅ Complete | `before_value`, `after_value`, `change_value`, `percent_change`, `conclusion`, `result_summary` |
| Android Connectivity Fix | ✅ Complete | `EXPO_PUBLIC_API_URL` via `.env`; physical device verified |
| React Native Frontend | ✅ Complete | All major endpoints integrated; occurrence-aware UI; Lab screen stable |
| My Profile Screen | ✅ Complete | Owner profile, privacy controls, correct logout location |
| Check-in History UI | ✅ Complete | `GET /api/v1/checkins` connected to Today screen |
| Procrastination Event History UI | ✅ Complete | `GET /api/v1/procrastination` connected to Delay Log screen |
| Privacy Audit | ✅ Verified | Backend correctly withholds private values; `null` wire format noted |
| **Test Suite** | ✅ Passing | **94 automated backend tests passing** + TypeScript 0 errors |

---

## FocusLoop

**Track → Understand → Act → Measure → Improve**

> **Learn what makes YOU productive.**
