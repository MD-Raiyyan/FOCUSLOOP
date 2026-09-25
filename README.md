# FocusLoop

> **Learn what makes YOU productive.**

FocusLoop is an Android-first personal productivity and behavioral-learning app that turns everyday behavior data into **understanding, experiments, measurement, and improvement**.

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

## FocusLoop

**Track → Understand → Act → Measure → Improve**

> **Learn what makes YOU productive.**
