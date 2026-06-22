"""角色出图任务 Markdown+JSON 解析单元测试。"""
from app.core.drama.character_image_tasks import (
    FENCE_CARD_PROMPT,
    FENCE_IMAGE_TASKS,
    FENCE_LOOK_PROMPT,
    extract_fenced_blocks,
    parse_character_image_tasks,
)


SAMPLE_REPLY = f"""
### ReAct 执行记录
Step 1 done.

### 小雪 · 定妆 Prompt

```{FENCE_LOOK_PROMPT}
single unified illustration, young woman, silver twin tails, school uniform
```

### 小雪 · 角色卡 Prompt

```{FENCE_CARD_PROMPT}
character reference sheet, 16:9, multiple expressions, silver twin tails
```

```{FENCE_IMAGE_TASKS}
[
  {{
    "task_id": "look",
    "character_name": "小雪",
    "label": "小雪·定妆图",
    "aspect_ratio": "3:4",
    "prompt_ref": "look-prompt",
    "negative_en": "turn-around, blurry",
    "image_count": 1
  }},
  {{
    "task_id": "card",
    "character_name": "小雪",
    "label": "小雪·角色卡",
    "aspect_ratio": "16:9",
    "prompt_ref": "card-prompt",
    "negative_en": "not 16:9, blurry",
    "image_count": 1
  }}
]
```
"""


def test_extract_fenced_blocks():
    blocks = extract_fenced_blocks(SAMPLE_REPLY)
    assert FENCE_LOOK_PROMPT in blocks
    assert "silver twin tails" in blocks[FENCE_LOOK_PROMPT]
    assert FENCE_CARD_PROMPT in blocks
    assert FENCE_IMAGE_TASKS in blocks


def test_parse_character_image_tasks():
    out = parse_character_image_tasks(SAMPLE_REPLY)
    assert out["ready"] is True
    assert len(out["tasks"]) == 2
    look = out["tasks"][0]
    assert look["task_id"] == "look"
    assert look["aspect_ratio"] == "3:4"
    assert "silver twin tails" in look["prompt_markdown"]
    assert look["negative_en"] == "turn-around, blurry"
    card = out["tasks"][1]
    assert card["aspect_ratio"] == "16:9"
    assert "multiple expressions" in card["prompt_markdown"]


def test_parse_missing_tasks_json():
    reply = f"```{FENCE_LOOK_PROMPT}\ntest prompt\n```"
    out = parse_character_image_tasks(reply)
    assert out["ready"] is False
    assert any("character-image-tasks" in e for e in out["errors"])
