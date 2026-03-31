#!/usr/bin/env python3
"""Turn a manually extracted knowledge absorption result into normalized JSON.

Usage:
  python knowledge_digest.py input.json
  cat input.json | python knowledge_digest.py
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

DEFAULT = {
    "source_type": "mixed",
    "title": "",
    "summary": "",
    "score": {
        "reusability": 0,
        "stability": 0,
        "verifiability": 0,
        "implementability": 0,
        "leverage": 0,
        "total": 0,
    },
    "principles": [],
    "patterns": [],
    "assets": {
        "skills": [],
        "references": [],
        "scripts": [],
        "examples": [],
    },
    "next_actions": [],
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def compute_total(data: Dict[str, Any]) -> Dict[str, Any]:
    score = data.get("score", {})
    keys = [
        "reusability",
        "stability",
        "verifiability",
        "implementability",
        "leverage",
    ]
    score["total"] = sum(int(score.get(k, 0) or 0) for k in keys)
    data["score"] = score
    return data


def load_input() -> Dict[str, Any]:
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            return json.load(f)
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def main() -> None:
    user_data = load_input()
    merged = deep_merge(DEFAULT, user_data)
    merged = compute_total(merged)
    print(json.dumps(merged, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
