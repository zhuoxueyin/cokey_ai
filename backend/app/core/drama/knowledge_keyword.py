"""知识检索关键词提取与多字段打分。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# 标题 > 标签 > 摘要 > 正文
FIELD_WEIGHTS: Dict[str, float] = {
    "title": 3.0,
    "tags": 2.0,
    "summary": 1.5,
    "content": 1.0,
}

_STOPWORDS = frozenset(
    {
        "的", "了", "是", "在", "我", "你", "他", "她", "它", "我们", "你们",
        "他们", "这", "那", "一个", "一些", "可以", "需要", "进行", "以及",
        "或者", "如果", "因为", "所以", "但是", "然后", "已经", "还是", "什么",
        "怎么", "如何", "请", "帮", "一下", "继续", "确认", "进入", "阶段",
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    }
)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """从用户输入提取约 10 个检索关键词（中英文混合）。"""
    raw = (text or "").strip()
    if not raw:
        return []

    candidates: List[str] = []
    if len(raw) <= 48:
        candidates.append(raw)

    parts = re.split(r"[\s,，。！？；;、：:/\\|（）()【】\[\]「」\"'<>]+", raw)
    for part in parts:
        chunk = part.strip()
        if len(chunk) < 2:
            continue
        if chunk.lower() in _STOPWORDS:
            continue
        candidates.append(chunk)

    # 英文词
    for m in re.finditer(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", raw):
        w = m.group(0).lower()
        if w not in _STOPWORDS:
            candidates.append(w)

    # 中文 2~6 字片段
    if re.search(r"[\u4e00-\u9fff]", raw):
        for m in re.finditer(r"[\u4e00-\u9fff]{2,8}", raw):
            seg = m.group(0)
            candidates.append(seg)
            if len(seg) > 4:
                for i in range(len(seg) - 1):
                    sub = seg[i:i + 2]
                    if sub not in _STOPWORDS:
                        candidates.append(sub)

    # 去重保序，优先较长词
    seen: set[str] = set()
    ordered: List[str] = []
    for term in sorted(candidates, key=len, reverse=True):
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(term)

    return ordered[:max_keywords]


def score_entry_keywords(doc: Dict[str, Any], keywords: List[str]) -> float:
    """多维度关键词匹配：标题 / 标签 / 摘要 / 正文。"""
    if not keywords:
        return 0.0

    title = str(doc.get("title") or "")
    summary = str(doc.get("summary") or "")
    content = str(doc.get("content_markdown") or "")
    tags = [str(t) for t in (doc.get("tags") or [])]

    score = 0.0
    for kw in keywords:
        kw_l = kw.lower()
        if kw_l in title.lower() or kw in title:
            score += FIELD_WEIGHTS["title"]
        tag_hit = any(kw_l in t.lower() or kw in t for t in tags)
        if tag_hit:
            score += FIELD_WEIGHTS["tags"]
        if kw_l in summary.lower() or kw in summary:
            score += FIELD_WEIGHTS["summary"]
        if kw_l in content.lower() or kw in content:
            score += FIELD_WEIGHTS["content"]

    return score


def rank_by_keyword_scores(
    docs: List[Dict[str, Any]],
    keywords: List[str],
) -> List[Tuple[float, Dict[str, Any]]]:
    scored = [(score_entry_keywords(d, keywords), d) for d in docs]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
