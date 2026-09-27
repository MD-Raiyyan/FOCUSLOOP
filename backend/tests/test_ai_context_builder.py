import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.procrastination import ProcrastinationEvent
from app.models.behavior import BehaviorPattern, BehaviorProfile
from app.models.experiment import Experiment, ExperimentResult
from app.models.chat import Conversation, Message
from app.ai.context_builder import AIContextBuilder
from app.ai.llm import llm_service
from app.ai.prompts import SYSTEM_EXPLAINER_PROMPT, CHAT_COMPANION_PROMPT
from app.schemas.ai import AIContext


def test_context_builder_user_scoping_and_privacy(db_session, test_user):
    """Verifies AI context is strictly isolated to the authenticated user."""
    # Create User B
    user_b = User(
        id="00000000-0000-0000-0000-000000000002",
        name="User B",
        email="user_b@focusloop.local",
        username="user_b",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()

    # User B has a private pattern and experiment
    pattern_b = BehaviorPattern(
        user_id=user_b.id,
        pattern_type="private_b_pattern",
        title="User B Secret Friction",
        description="Private description for User B",
        status="active",
        confidence="high",
        sample_size=15,
    )
    db_session.add(pattern_b)

    exp_b = Experiment(
        user_id=user_b.id,
        title="User B Secret Experiment",
        description="Secret experiment description",
        hypothesis="Secret hypothesis",
        target_metric="completion_rate",
        start_date="2026-09-01",
    )
    db_session.add(exp_b)
    db_session.commit()

    # Build context for test_user (User A)
    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="What are my patterns?")

    assert isinstance(ctx, AIContext)
    assert ctx.user_id == test_user.id
    assert ctx.user_name == test_user.name

    # Ensure NO data from User B is leaked into User A's context
    pattern_titles = [p["title"] for p in ctx.patterns]
    assert "User B Secret Friction" not in pattern_titles

    exp_titles = [e["title"] for e in ctx.experiments]
    assert "User B Secret Experiment" not in exp_titles


def test_context_builder_question_filtering_procrastination_and_evening(db_session, test_user):
    """
    Verifies that asking about evening procrastination selects evening-specific
    and delay evidence while filtering out unrelated scopes.
    """
    # Create morning and evening tasks for test_user
    task_eve = Task(
        user_id=test_user.id,
        name="Night Coding",
        planned_time="20:00",
        target_duration_minutes="45",
    )
    task_morn = Task(
        user_id=test_user.id,
        name="Morning Journal",
        planned_time="08:00",
        target_duration_minutes="15",
    )
    db_session.add_all([task_eve, task_morn])
    db_session.commit()

    # Checkin with start delay for evening task
    checkin_eve = TaskCheckin(
        user_id=test_user.id,
        task_id=task_eve.id,
        date="2026-09-26",
        status="partial",
        duration_minutes=20,
        start_delay_minutes=35,
    )
    # Procrastination event
    proc_event = ProcrastinationEvent(
        user_id=test_user.id,
        task_id=task_eve.id,
        started_at=datetime.utcnow() - timedelta(minutes=40),
        ended_at=datetime.utcnow() - timedelta(minutes=10),
        duration_seconds=1800,
        trigger_reason="Mindful Delay Check",
        user_confirmed=True,
    )
    # Evening pattern
    pattern_eve = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="time_of_day_delay",
        title="Evening Start Resistance",
        description="Average delay is notably higher during evening tasks.",
        status="active",
        confidence="high",
        sample_size=12,
        supporting_metrics={"evening_avg_delay": 35},
    )
    db_session.add_all([checkin_eve, proc_event, pattern_eve])
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="Why do I keep procrastinating at night?")

    assert "procrastination_delay" in ctx.classified_intents
    assert "time_of_day" in ctx.classified_intents

    # Evening performance is specifically surfaced
    metrics = ctx.metrics
    assert "evening_performance" in metrics
    assert "start_delay" in metrics
    assert metrics["start_delay"]["average_start_delay_minutes"] == 35.0
    assert "procrastination_episodes" in metrics
    assert metrics["procrastination_episodes"]["count"] >= 1

    # Evening pattern is included with provenance and confidence
    assert len(ctx.patterns) >= 1
    matched = next((p for p in ctx.patterns if p["title"] == "Evening Start Resistance"), None)
    assert matched is not None
    assert matched["confidence"] == "high"
    assert matched["sample_size"] == 12
    assert matched["source"] == "behavior_engine.pattern_detector"


def test_context_builder_question_filtering_experiment_evaluation(db_session, test_user):
    """
    Verifies that asking about experiments selects experiment hypotheses,
    baselines, and measured before/after results without leaking into unrelated fields.
    """
    exp = Experiment(
        user_id=test_user.id,
        title="10-Minute Evening Buffer",
        description="Shift evening start time earlier",
        hypothesis="Starting with a 5-minute kickoff will lower evening start latency",
        intervention_type="micro_commitment",
        target_metric="average_start_delay_minutes",
        baseline_value=35.0,
        target_value=15.0,
        start_date="2026-09-20",
        status="completed",
    )
    db_session.add(exp)
    db_session.commit()

    res = ExperimentResult(
        experiment_id=exp.id,
        metric_name="average_start_delay_minutes",
        before_value=35.0,
        after_value=18.0,
        change_value=-17.0,
        percent_change=-48.6,
        conclusion="positive",
        result_summary="Experiment '10-Minute Evening Buffer' evaluated. Observed 48.6% drop in delay.",
    )
    db_session.add(res)
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="Did my last experiment work?")

    assert "experiment_evaluation" in ctx.classified_intents
    assert len(ctx.experiments) >= 1
    exp_data = ctx.experiments[0]
    assert exp_data["title"] == "10-Minute Evening Buffer"
    assert exp_data["hypothesis"] == "Starting with a 5-minute kickoff will lower evening start latency"
    assert exp_data["status"] == "completed"

    # Verifies authoritative numerical result
    results = exp_data["results"]
    assert len(results) == 1
    assert results[0]["before_value"] == 35.0
    assert results[0]["after_value"] == 18.0
    assert results[0]["conclusion"] == "positive"
    assert results[0]["provenance"] == "backend_experiment_evaluator"


def test_context_builder_question_filtering_improvement_trend(db_session, test_user):
    """Verifies asking 'Am I improving?' includes trajectory metrics and level milestones."""
    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="Am I improving over time?")

    assert "improvement_trend" in ctx.classified_intents
    assert "trajectory" in ctx.metrics
    traj = ctx.metrics["trajectory"]
    assert "improvement_score" in traj
    assert "consistency_score" in traj
    assert "behavior_score" in traj
    assert traj["provenance"] == "behavior_engine.continuous_progress"


def test_context_builder_telemetry_missing_data_honesty(db_session, test_user):
    """Verifies unmeasured screen usage and sleep are honestly reported as unavailable."""
    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="Analyze my distractions")

    telemetry = ctx.telemetry_status
    assert "screen_usage" in telemetry
    assert telemetry["screen_usage"]["status"] == "unavailable"
    assert "not enabled or recorded" in telemetry["screen_usage"]["reason"]

    assert "sleep_tracking" in telemetry
    assert telemetry["sleep_tracking"]["status"] == "unavailable"
    assert "not synced or recorded" in telemetry["sleep_tracking"]["reason"]

    # Limitations explicitly state telemetry unavailability
    assert any("Screen usage telemetry is unavailable" in lim for lim in ctx.limitations)
    assert any("Sleep telemetry is unavailable" in lim for lim in ctx.limitations)


def test_context_builder_conversation_context_boundary(db_session, test_user):
    """
    Verifies that conversation history is preserved but explicitly quarantined
    as user self-report rather than verified backend truth.
    """
    history = [
        {"role": "user", "content": "I feel like I always procrastinate at night."},
        {"role": "assistant", "content": "Let's check your verified focus records."},
    ]

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(
        question="Can you help me?",
        conversation_history=history,
    )

    convo_ctx = ctx.conversation_context
    assert "recent_messages" in convo_ctx
    assert len(convo_ctx["recent_messages"]) == 2
    assert "evidential_boundary_rule" in convo_ctx
    rule = convo_ctx["evidential_boundary_rule"]
    assert "NOT verified backend facts" in rule


def test_llm_prompts_and_service_grounding_constraints():
    """Verifies system prompts prohibit inventing measurements and enforce observational tone."""
    # Explainer prompt constraints
    assert "Do NOT recalculate, modify, or contradict backend metrics" in SYSTEM_EXPLAINER_PROMPT
    assert "NEVER invent unmeasured statistics" in SYSTEM_EXPLAINER_PROMPT
    assert "Distinguish Measured Evidence from Perceptions and Hypotheses" in SYSTEM_EXPLAINER_PROMPT
    assert "Do NOT diagnose medical or psychological conditions" in SYSTEM_EXPLAINER_PROMPT
    assert "Current vs Historical/Resolved Patterns" in SYSTEM_EXPLAINER_PROMPT
    assert "lazy" in SYSTEM_EXPLAINER_PROMPT

    # Companion prompt constraints
    assert "Do not invent metrics" in CHAT_COMPANION_PROMPT
    assert "Distinguish user self-reported perceptions from measured backend evidence" in CHAT_COMPANION_PROMPT


def test_context_builder_current_vs_resolved_patterns(db_session, test_user):
    """
    Part 9: Verifies AIContextBuilder clearly separates:
    - current_patterns: active, improving, weakening
    - resolved_patterns: resolved, archived
    and includes explicit non-active guidance for resolved patterns.
    """
    p_active = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Active delay",
        status="active",
        confidence="moderate",
        sample_size=10,
    )
    p_improving = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction (Improving)",
        description="Delay improving",
        status="improving",
        confidence="moderate",
        sample_size=8,
    )
    p_resolved = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="primary_distraction",
        title="Frequent Transition to Instagram (Resolved)",
        description="Resolved distraction",
        status="resolved",
        confidence="low",
        sample_size=12,
    )
    db_session.add_all([p_active, p_improving, p_resolved])
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="What are my current focus habits and patterns?")

    # 1. Separated payloads exist
    assert hasattr(ctx, "current_patterns")
    assert hasattr(ctx, "resolved_patterns")

    current_ids = [p["id"] for p in ctx.current_patterns]
    resolved_ids = [p["id"] for p in ctx.resolved_patterns]

    assert p_active.id in current_ids
    assert p_improving.id in current_ids
    assert p_resolved.id not in current_ids

    assert p_resolved.id in resolved_ids
    assert p_active.id not in resolved_ids
    assert p_improving.id not in resolved_ids

    # 2. Resolved pattern has explicit guidance note
    resolved_entry = next(p for p in ctx.resolved_patterns if p["id"] == p_resolved.id)
    assert resolved_entry["is_current"] is False
    assert resolved_entry["lifecycle_category"] == "historical_resolved"
    assert "HISTORICAL / RESOLVED" in resolved_entry["explanation_guidance"]



def test_chat_endpoints_end_to_end_with_context_builder(client):
    """
    Verifies /chat/explain, /chat/conversations, and /chat/conversations/{id}/messages
    run end-to-end with the new structured AIContext.
    """
    # 1. POST /chat/explain with question-relevant intent
    exp_resp = client.post(
        "/api/v1/chat/explain",
        json={"question": "Why do I delay task starts in the afternoon?"},
    )
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert "explanation" in exp_data
    assert "deterministic_context" in exp_data
    det_ctx = exp_data["deterministic_context"]
    assert "metrics" in det_ctx
    assert "user_id" in det_ctx
    assert "limitations" in det_ctx

    # 2. POST /chat/conversations to create or get active conversation
    convo_resp = client.post("/api/v1/chat/conversations")
    assert convo_resp.status_code == 201
    convo = convo_resp.json()
    convo_id = convo["id"]
    assert "messages" in convo

    # 3. POST /chat/conversations/{id}/messages
    msg_resp = client.post(
        f"/api/v1/chat/conversations/{convo_id}/messages",
        json={"content": "Did my recent focus experiment succeed?"},
    )
    assert msg_resp.status_code == 200
    msg_data = msg_resp.json()
    assert msg_data["conversation_id"] == convo_id
    assert msg_data["sender"] == "assistant"
    assert len(msg_data["content"]) > 10

    # 4. Verify conversation persistence via GET
    get_convo_resp = client.get(f"/api/v1/chat/conversations/{convo_id}")
    assert get_convo_resp.status_code == 200
    persisted_convo = get_convo_resp.json()
    assert len(persisted_convo["messages"]) >= 2
    senders = [m["sender"] for m in persisted_convo["messages"]]
    assert "user" in senders
    assert "assistant" in senders
