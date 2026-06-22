"""从用户消息推断创作阶段（兼容层 → agent_creation_pipeline）。"""
from app.core.drama.agent_creation_pipeline import (
    analyze_creation_intent,
    infer_stage_from_message,
    stage_switch_reason,
)

__all__ = [
    "analyze_creation_intent",
    "infer_stage_from_message",
    "stage_switch_reason",
]
