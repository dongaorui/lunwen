import re


CODE_START_MARKERS = [
    "import pulp",
    "from pulp import",
    "def build_model",
    "model = pulp.LpProblem",
    "model= pulp.LpProblem",
]

TRAILING_TEXT_MARKERS = [
    "\n# Explanation",
    "\nExplanation:",
    "\nNotes:",
    "\n```",
]


def _normalize_code(code):
    cleaned = code.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:python|py)?\s*\n?", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned + "\n" if cleaned else ""


def _strip_trailing_explanation(code):
    stop_positions = [code.find(marker) for marker in TRAILING_TEXT_MARKERS if code.find(marker) > 0]
    if stop_positions:
        return code[: min(stop_positions)]
    return code


def extract_python_code(text):
    """Extract Python code from an LLM response without executing it."""
    if text is None:
        return ""

    python_blocks = re.findall(r"```(?:python|py)\s*\n(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if python_blocks:
        return _normalize_code(python_blocks[0])

    any_blocks = re.findall(r"```\s*\n(.*?)```", text, flags=re.DOTALL)
    if any_blocks:
        return _normalize_code(any_blocks[0])

    starts = [text.find(marker) for marker in CODE_START_MARKERS if text.find(marker) >= 0]
    if starts:
        candidate = text[min(starts):]
        return _normalize_code(_strip_trailing_explanation(candidate))

    return ""


def extract_code(text):
    return extract_python_code(text)
