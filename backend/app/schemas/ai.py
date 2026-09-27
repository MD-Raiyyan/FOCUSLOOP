from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIContext(BaseModel):
    """
    Structured, privacy-safe, evidence-backed AI context contract.
    The backend is the sole source of truth; all quantitative evidence
    is pre-computed and filtered deterministically before reaching the LLM.
    """
    user_id: str
    user_name: str
    user_question: Optional[str] = None
    classified_intents: List[str] = Field(default_factory=list)
    time_window: Dict[str, Any] = Field(default_factory=dict)

    # Question-relevant evidence sections
    user_context: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    behavior_profile: Dict[str, Any] = Field(default_factory=dict)
    experiments: List[Dict[str, Any]] = Field(default_factory=list)
    telemetry_status: Dict[str, Any] = Field(default_factory=dict)
    conversation_context: Dict[str, Any] = Field(default_factory=dict)

    # Evidentiary boundaries and limitations
    limitations: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable dictionary representation."""
        return self.model_dump()
