from datetime import datetime
from typing import Dict, Any, Optional
from app.models.behavior import BehaviorPattern


def build_pattern_snapshot(pattern: BehaviorPattern) -> Dict[str, Any]:
    """
    Creates an immutable, decision-relevant snapshot of a BehaviorPattern
    at the time an Experiment is created.
    
    Contains NO raw evidence (no checkins, no raw event streams).
    Captures only the derived metrics and pattern state that informed
    the experiment decision.
    """
    metrics = pattern.supporting_metrics or {}
    
    # Extract decision-relevant summary metrics, explicitly excluding heavy raw/daily time series arrays
    decision_metrics = {
        "metric_name": metrics.get("metric_name"),
        "unit": metrics.get("unit"),
        "historical_window": metrics.get("historical_window"),
        "recent_window": metrics.get("recent_window"),
        "context_comparison": metrics.get("context_comparison"),
        "effective_recent_sample_size": metrics.get("effective_recent_sample_size"),
        "distinct_days": metrics.get("distinct_days"),
        "recent_distinct_days": metrics.get("recent_distinct_days"),
        "first_observed_date": metrics.get("first_observed_date"),
        "last_observed_date": metrics.get("last_observed_date"),
        "trend": metrics.get("trend"),
        "insufficient_evidence": metrics.get("insufficient_evidence"),
        "insufficient_current_evidence": metrics.get("insufficient_current_evidence"),
    }
    clean_metrics = {k: v for k, v in decision_metrics.items() if v is not None}

    return {
        "pattern_id": pattern.id,
        "pattern_type": pattern.pattern_type,
        "pattern_title": pattern.title,
        "pattern_description": pattern.description,
        "confidence": pattern.confidence,
        "sample_size": pattern.sample_size,
        "status": pattern.status,
        "first_detected": pattern.first_detected.isoformat() if pattern.first_detected else None,
        "last_detected": pattern.last_detected.isoformat() if pattern.last_detected else None,
        "supporting_metrics": clean_metrics,
        "snapshot_created_at": datetime.utcnow().isoformat(),
    }
