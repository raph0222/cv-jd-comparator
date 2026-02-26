import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_match_response(content: str) -> Dict[str, Any]:
    """Extract and parse a JSON object from model output."""

    def _try_json(value: str):
        try:
            return json.loads(value)
        except Exception:
            return None

    content = (content or "").strip()
    if not content:
        return {}

    if content.startswith("```"):
        content = re.sub(r"^```\w*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)
        content = content.strip()

    result = _try_json(content)

    if result is None:
        start = content.find("{")
        if start != -1:
            depth = 0
            end = -1
            for i in range(start, len(content)):
                ch = content[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end != -1:
                result = _try_json(content[start:end])

    if result is None:
        try:
            import ast

            literal = ast.literal_eval(content)
            if isinstance(literal, dict):
                result = literal
        except Exception:
            result = None

    if not isinstance(result, dict):
        snippet = content[:500].replace("\n", "\\n")
        logger.error("Model response is not a dict. Raw content snippet: %s", snippet)
        raise ValueError("Model response is not a JSON object.")

    normalized: Dict[str, Any] = {}
    for raw_key, value in result.items():
        key = str(raw_key).strip()
        if key.startswith('"') and key.endswith('"') and len(key) > 2:
            key = key[1:-1]
        normalized[key] = value
    return normalized
