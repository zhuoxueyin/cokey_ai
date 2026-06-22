"""Skill 标准规范：SKILL.md frontmatter + 八段式 Markdown。"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED_SECTIONS = [
    "一、技能简介",
    "二、适用场景",
    "三、输入条件",
    "四、核心执行流程",
    "五、输出标准",
    "六、异常兜底",
    "七、约束禁忌",
    "八、版本记录",
]

REQUIRED_META_KEYS = ("skill_name", "skill_id", "version", "author", "update_time", "tag")


def repo_skills_root() -> Path:
    """代码库 skills/ 根目录（项目根/skills）。"""
    return Path(__file__).resolve().parents[4] / "skills"


# skill_code → skills/ 子目录（内置 Skill 未写 repo_path 时的兜底）
SKILL_CODE_REPO_FOLDER: Dict[str, str] = {
    "skill.intake": "skill_intake",
    "skill.concept": "skill_concept",
    "skill.character": "skill_character",
    "skill.scene": "skill_scene",
    "skill.storyboard": "skill_storyboard",
    "skill.production": "skill_production",
}


def resolve_repo_folder(skill_code: str, repo_path: Optional[str] = None) -> Optional[str]:
    """解析代码库子目录：优先 repo_path，其次内置映射。"""
    folder = (repo_path or "").strip()
    if folder:
        return folder
    return SKILL_CODE_REPO_FOLDER.get(skill_code or "")


def skill_spec_template(
    *,
    skill_name: str = "技能名称",
    skill_id: str = "skill.example",
    author: str = "xxx",
    tag: str = "标签",
) -> str:
    today = date.today().isoformat()
    return f"""---
skill_name: {skill_name}
skill_id: {skill_id}
version: 1.0.0
author: {author}
update_time: {today}
tag: {tag}
---

# 一、技能简介
（一段话描述技能目标与产出标准）

# 二、适用场景
1. 适用场景一
2. 适用场景二
不适用场景：xxx

# 三、输入条件
1. 输入项一
2. 输入项二

# 四、核心执行流程
1. 步骤一
2. 步骤二
3. 步骤三

# 五、输出标准
1. 输出标准一
2. 输出标准二

# 六、异常兜底
1. 异常情况及处理方式

# 七、约束禁忌
禁止 xxx

# 八、版本记录
| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 1.0.0 | {today} | 首次定稿 | {author} |
"""


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """解析 YAML frontmatter（简单 key: value，不支持嵌套）。"""
    raw = (text or "").strip()
    if not raw.startswith("---"):
        return {}, raw
    m = FRONTMATTER_RE.match(raw + ("\n" if not raw.endswith("\n") else ""))
    if not m:
        return {}, raw
    meta: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip()
    body = raw[m.end() :].strip()
    return meta, body


def build_skill_markdown(meta: Dict[str, str], body: str) -> str:
    lines = ["---"]
    for key in REQUIRED_META_KEYS:
        if meta.get(key):
            lines.append(f"{key}: {meta[key]}")
    for key, val in meta.items():
        if key not in REQUIRED_META_KEYS and val:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body.strip() + "\n"


def validate_skill_content(text: str, *, skill_code: Optional[str] = None) -> None:
    meta, body = parse_frontmatter(text)
    missing_meta = [k for k in REQUIRED_META_KEYS if not meta.get(k)]
    if missing_meta:
        raise ValueError(f"SKILL 元数据缺失: {', '.join(missing_meta)}")
    if skill_code and meta.get("skill_id") and meta["skill_id"] != skill_code:
        raise ValueError(f"frontmatter skill_id ({meta['skill_id']}) 与 Code ({skill_code}) 不一致")
    for title in REQUIRED_SECTIONS:
        if title not in body:
            raise ValueError(f"缺少必选章节: {title}")


def skill_content_to_system_prompt(text: str) -> str:
    """Agent 注入用：完整 SKILL 正文（含 frontmatter）。"""
    return (text or "").strip()


def enrich_skill_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """从 skill_content_md 派生 name / description / system_markdown 等。"""
    out = dict(data)
    content = out.get("skill_content_md") or out.get("system_markdown") or ""
    if not content.strip():
        return out

    meta, body = parse_frontmatter(content)
    if meta.get("skill_name") and not out.get("name"):
        out["name"] = meta["skill_name"]
    if meta.get("skill_id") and not out.get("skill_code"):
        out["skill_code"] = meta["skill_id"]
    if meta.get("tag") and not out.get("description"):
        out["description"] = meta["tag"]

    out["skill_meta"] = meta
    out["skill_content_md"] = build_skill_markdown(meta, body) if meta else content.strip()
    out["system_markdown"] = skill_content_to_system_prompt(out["skill_content_md"])
    if not out.get("user_markdown"):
        out["user_markdown"] = "## 用户输入\n{{message}}\n\n请严格按 SKILL 规范执行。"
    return out


def scan_repo_skill_folders(root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """扫描代码库 skills/*/ 目录，要求 SKILL.md + scripts/。"""
    base = root or repo_skills_root()
    if not base.is_dir():
        return []

    items: List[Dict[str, Any]] = []
    for folder in sorted(base.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        skill_md = folder / "SKILL.md"
        scripts_dir = folder / "scripts"
        if not skill_md.is_file():
            continue
        if not scripts_dir.is_dir():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _ = parse_frontmatter(text)
        script_files = sorted(
            p.name for p in scripts_dir.iterdir() if p.is_file() and not p.name.startswith(".")
        )
        items.append(
            {
                "folder": folder.name,
                "path": str(folder.relative_to(base.parent)),
                "skill_id": meta.get("skill_id") or folder.name,
                "skill_name": meta.get("skill_name") or folder.name,
                "version": meta.get("version", ""),
                "tag": meta.get("tag", ""),
                "author": meta.get("author", ""),
                "update_time": meta.get("update_time", ""),
                "script_files": script_files,
                "valid": bool(meta.get("skill_id") and meta.get("skill_name")),
            }
        )
    return items


def load_repo_skill(folder: str, root: Optional[Path] = None) -> Dict[str, Any]:
    """从代码库目录加载 Skill 为 create payload。"""
    base = root or repo_skills_root()
    skill_dir = base / folder
    skill_md = skill_dir / "SKILL.md"
    scripts_dir = skill_dir / "scripts"

    if not skill_md.is_file():
        raise ValueError(f"缺少 SKILL.md: {folder}")
    if not scripts_dir.is_dir():
        raise ValueError(f"缺少 scripts/ 目录: {folder}")

    content = skill_md.read_text(encoding="utf-8")
    validate_skill_content(content)
    meta, _ = parse_frontmatter(content)
    script_files = sorted(
        p.name for p in scripts_dir.iterdir() if p.is_file() and not p.name.startswith(".")
    )

    payload = {
        "skill_code": meta["skill_id"],
        "name": meta["skill_name"],
        "stage": "production",
        "source": "repo",
        "source_type": "repo",
        "repo_path": folder,
        "skill_content_md": content.strip(),
        "script_files": script_files,
        "description": meta.get("tag", ""),
    }
    return enrich_skill_payload(payload)
