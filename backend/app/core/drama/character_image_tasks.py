"""角色阶段出图任务解析：Markdown 主力 prompt + JSON 任务参数。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

# Markdown fenced 块语言标识（模型输出 · 主力生图 prompt）
FENCE_LOOK_PROMPT = "look-prompt"
FENCE_CARD_PROMPT = "card-prompt"

# JSON 任务块（平台一键出图 · 尺寸/负向/引用）
FENCE_IMAGE_TASKS = "character-image-tasks"

FENCE_PATTERN = re.compile(
    r"```(?P<lang>[\w-]+)\s*\n(?P<body>.*?)```",
    re.DOTALL,
)

VALID_TASK_IDS = frozenset({"look", "card"})


def extract_fenced_blocks(content: str) -> Dict[str, str]:
    """提取回复中所有 fenced 块，key=lang tag。"""
    blocks: Dict[str, str] = {}
    for match in FENCE_PATTERN.finditer(content or ""):
        lang = (match.group("lang") or "").strip().lower()
        body = (match.group("body") or "").strip()
        if lang and body:
            blocks[lang] = body
    return blocks


def parse_image_tasks_json(raw: str) -> List[Dict[str, Any]]:
    """解析 character-image-tasks JSON 数组。"""
    text = (raw or "").strip()
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, dict):
        tasks = data.get("tasks") or data.get("image_tasks")
        if isinstance(tasks, list):
            return tasks
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("character-image-tasks 须为 JSON 数组或含 tasks 字段的对象")


def resolve_prompt_markdown(
    task: Dict[str, Any],
    prompts: Dict[str, str],
) -> str:
    """按 prompt_ref 或 task_id 默认映射，解析主力 Markdown prompt。"""
    ref = (task.get("prompt_ref") or "").strip().lower()
    if ref and ref in prompts:
        return prompts[ref]
    task_id = (task.get("task_id") or task.get("task") or "").strip().lower()
    default_ref = {
        "look": FENCE_LOOK_PROMPT,
        "card": FENCE_CARD_PROMPT,
    }.get(task_id, "")
    if default_ref and default_ref in prompts:
        return prompts[default_ref]
    positive = (task.get("positive_en") or task.get("positive") or "").strip()
    return positive


def parse_character_image_tasks(content: str) -> Dict[str, Any]:
    """
    从助手回复解析出图任务。

    返回:
      prompts: fenced Markdown 块
      tasks: 合并 prompt_markdown 后的任务列表（可直接提交出图）
      errors: 非致命解析问题
    """
    blocks = extract_fenced_blocks(content)
    prompts = {
        k: v
        for k, v in blocks.items()
        if k in (FENCE_LOOK_PROMPT, FENCE_CARD_PROMPT)
    }

    errors: List[str] = []
    raw_tasks: List[Dict[str, Any]] = []
    tasks_json_raw = blocks.get(FENCE_IMAGE_TASKS, "")
    if tasks_json_raw:
        try:
            raw_tasks = parse_image_tasks_json(tasks_json_raw)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"character-image-tasks 解析失败: {exc}")
    elif prompts:
        errors.append("缺少 character-image-tasks JSON，仅有 Markdown prompt 块")

    merged: List[Dict[str, Any]] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            errors.append("任务项须为对象")
            continue
        task_id = (item.get("task_id") or item.get("task") or "").strip().lower()
        prompt_md = resolve_prompt_markdown(item, prompts)
        if not prompt_md:
            errors.append(f"任务 {task_id or '?'} 未找到 prompt_ref 对应 Markdown 块")
        entry = {
            **item,
            "task_id": task_id,
            "prompt_markdown": prompt_md,
            "aspect_ratio": item.get("aspect_ratio") or item.get("size") or "",
            "negative_en": (item.get("negative_en") or item.get("negative") or "").strip(),
            "image_count": int(item.get("image_count") or 1),
        }
        if task_id and task_id not in VALID_TASK_IDS:
            errors.append(f"未知 task_id: {task_id}")
        merged.append(entry)

    return {
        "prompts": prompts,
        "raw_tasks": raw_tasks,
        "tasks": merged,
        "errors": errors,
        "ready": bool(merged) and all(t.get("prompt_markdown") for t in merged) and not errors,
    }


def build_image_task_json_block(
    tasks: List[Dict[str, Any]],
) -> str:
    """生成 character-image-tasks fenced JSON（不含外层 fence）。"""
    payload = []
    for t in tasks:
        payload.append(
            {
                "task_id": t.get("task_id"),
                "character_name": t.get("character_name", ""),
                "label": t.get("label", ""),
                "aspect_ratio": t.get("aspect_ratio", ""),
                "prompt_ref": t.get("prompt_ref", ""),
                "negative_en": t.get("negative_en", ""),
                "image_count": t.get("image_count", 1),
            }
        )
    return json.dumps(payload, ensure_ascii=False, indent=2)
