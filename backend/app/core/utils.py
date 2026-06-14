from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_trace_id() -> str:
    import uuid
    return f"trace_{uuid.uuid4().hex}"


def generate_task_id() -> str:
    import uuid
    return f"task_{uuid.uuid4().hex}"


def generate_session_id() -> str:
    import uuid
    return f"sess_{uuid.uuid4().hex}"


def generate_uuid() -> str:
    import uuid
    return uuid.uuid4().hex


def dict_to_masked(data: Dict[str, Any], sensitive_keys: Optional[list] = None) -> Dict[str, Any]:
    if sensitive_keys is None:
        sensitive_keys = ["api_key", "password", "token", "secret", "key", "authorization"]
    
    result = {}
    for k, v in data.items():
        if isinstance(v, dict):
            result[k] = dict_to_masked(v, sensitive_keys)
        elif isinstance(v, list):
            result[k] = [dict_to_masked(item, sensitive_keys) if isinstance(item, dict) else item for item in v]
        elif isinstance(k, str) and any(sk in k.lower() for sk in sensitive_keys):
            result[k] = "***"
        else:
            result[k] = v
    return result


def parse_chain(chain: list) -> str:
    return " -> ".join(chain) if chain else ""
