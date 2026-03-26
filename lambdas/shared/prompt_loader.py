"""
Prompt Loader
─────────────────────────────────────────────────────────────────────────────
Reads YAML prompt template files and renders Jinja2 variables into the final
prompt strings used by each AI integration.

Usage:
    from prompt_loader import load_prompt, validate_response

    cfg = load_prompt("signal_validator", {
        "symbol": "INFY.NS",
        "name": "Infosys Ltd",
        "signal": "BUY",
        ...
    })
    # cfg["user"]          → rendered prompt string
    # cfg["model"]         → model ID from YAML
    # cfg["temperature"]   → temperature from YAML
    # cfg["max_tokens"]    → max_tokens from YAML

    validate_response("signal_validator", response_dict)  # raises on invalid

Template files live in:
    <project_root>/prompts/*.yaml
    <project_root>/prompts/*.txt   (plain text, no variables — e.g. Bedrock agent instruction)
─────────────────────────────────────────────────────────────────────────────
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template, StrictUndefined, UndefinedError

logger = logging.getLogger(__name__)

# ── Resolve prompts directory ─────────────────────────────────────────────────
# Works both locally (backend/prompt_loader.py → ../prompts/)
# and in Lambda layer  (shared/prompt_loader.py → ../prompts/ bundled alongside)
_HERE = Path(__file__).resolve().parent
_PROMPTS_DIR = _HERE.parent / "prompts"

# Allow override via env var (useful for Lambda packaging)
if os.environ.get("PROMPTS_DIR"):
    _PROMPTS_DIR = Path(os.environ["PROMPTS_DIR"])


# ── Internal helpers ──────────────────────────────────────────────────────────

@lru_cache(maxsize=32)
def _load_raw(name: str) -> dict:
    """Read and parse a YAML template file. Cached after first load."""
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Prompt template {name}.yaml must be a YAML mapping")
    return data


def _render(template_str: str, variables: dict, name: str) -> str:
    """Render a Jinja2 template string. Raises clearly on missing variables."""
    try:
        return Template(template_str, undefined=StrictUndefined).render(**variables)
    except UndefinedError as e:
        raise ValueError(
            f"Prompt template '{name}' is missing required variable: {e}"
        ) from e


# ── Public API ────────────────────────────────────────────────────────────────

def load_prompt(name: str, variables: dict | None = None) -> dict:
    """
    Load a prompt template by name and render variables into it.

    Args:
        name:      Template name (without .yaml extension), e.g. "signal_validator"
        variables: Dict of values to substitute into {{ variable }} placeholders.
                   Pass None or {} for templates with no placeholders.

    Returns:
        Dict with keys:
            user        – rendered user message string
            model       – model ID string (from YAML)
            temperature – float (from YAML)
            max_tokens  – int (from YAML)
            name        – template name
            version     – template version string
            guardrails  – list of guardrail strings
            output_schema – dict (may be empty)
    """
    variables = variables or {}
    raw = _load_raw(name)

    user_template = raw.get("user_template", "")
    rendered_user = _render(user_template, variables, name) if user_template else ""

    return {
        "user": rendered_user,
        "model": raw.get("model"),
        "temperature": raw.get("temperature", 0.2),
        "max_tokens": raw.get("max_tokens", 512),
        "name": raw.get("name", name),
        "version": raw.get("version", "unknown"),
        "guardrails": raw.get("guardrails", []),
        "output_schema": raw.get("output_schema", {}),
    }


def validate_response(name: str, response: dict) -> None:
    """
    Validate an AI response dict against the template's output_schema.

    Args:
        name:     Template name used to load the schema
        response: Dict returned by the AI (after JSON parsing)

    Raises:
        ValueError: With a descriptive message if validation fails
    """
    raw = _load_raw(name)
    schema = raw.get("output_schema", {})
    if not schema:
        return  # No schema defined — nothing to validate

    required_fields = schema.get("required", [])
    field_types = schema.get("field_types", {})

    # Check required fields present
    missing = [f for f in required_fields if f not in response]
    if missing:
        raise ValueError(
            f"AI response for '{name}' missing required fields: {missing}"
        )

    # Check enum constraints
    for field, type_spec in field_types.items():
        if field not in response:
            continue
        if isinstance(type_spec, str) and type_spec.startswith("enum:"):
            allowed = type_spec.split(":", 1)[1].split(",")
            val = response[field]
            if isinstance(val, str) and val not in allowed:
                raise ValueError(
                    f"Field '{field}' in '{name}' response has invalid value "
                    f"'{val}'. Allowed: {allowed}"
                )
        elif type_spec == "boolean" and not isinstance(response[field], bool):
            raise ValueError(
                f"Field '{field}' in '{name}' response must be boolean, "
                f"got {type(response[field]).__name__}"
            )
        elif type_spec == "array" and not isinstance(response[field], list):
            raise ValueError(
                f"Field '{field}' in '{name}' response must be an array, "
                f"got {type(response[field]).__name__}"
            )


def load_agent_instruction(filename: str) -> str:
    """
    Load a plain-text prompt file (no Jinja2 rendering).
    Used for Bedrock Agent instruction strings read at deploy time.

    Args:
        filename: File name relative to prompts/ dir, e.g. "trading_guru_agent.txt"

    Returns:
        The file contents as a string.
    """
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Agent instruction file not found: {path}")
    return path.read_text(encoding="utf-8")
