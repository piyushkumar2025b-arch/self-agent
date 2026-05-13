"""
cost_engine.py — model pricing, usage recording, and cost aggregation helpers.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any

# ── Pricing (USD per 1M tokens) ───────────────────────────────────────────────
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-20250514":    {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514":  {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input":  0.80,  "output":  4.00},
    "gpt-4o":                    {"input":  5.00, "output": 15.00},
    "gpt-4o-mini":               {"input":  0.15, "output":  0.60},
    "gemini-1.5-pro":            {"input":  3.50, "output": 10.50},
    "gemini-1.5-flash":          {"input":  0.075,"output":  0.30},
    "llama-3.1-70b":             {"input":  0.59, "output":  0.79},
    "mixtral-8x7b":              {"input":  0.24, "output":  0.24},
}


def _cost_for(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (
        input_tokens  / 1_000_000 * pricing["input"] +
        output_tokens / 1_000_000 * pricing["output"]
    )


def add_usage_record(
    log: list,
    *,
    model: str,
    agent: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Append a usage record to the mutable log list."""
    log.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "agent": agent,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    )


def get_session_costs(log: list) -> dict[str, dict[str, Any]]:
    """
    Aggregate per-model costs.
    Returns { model: { cost, calls, input_tokens, output_tokens } }
    """
    agg: dict[str, dict] = {}
    for record in log:
        m = record["model"]
        if m not in agg:
            agg[m] = {"cost": 0.0, "calls": 0, "input_tokens": 0, "output_tokens": 0}
        agg[m]["calls"] += 1
        agg[m]["input_tokens"] += record["input_tokens"]
        agg[m]["output_tokens"] += record["output_tokens"]
        agg[m]["cost"] += _cost_for(m, record["input_tokens"], record["output_tokens"])
    return agg


def get_total_cost(costs: dict) -> float:
    return sum(v["cost"] for v in costs.values())


def format_cost(value: float) -> str:
    if value < 0.0001:
        return "$0.00"
    if value < 0.01:
        return f"${value:.5f}"
    return f"${value:.4f}"


def reset_costs(session_state) -> None:
    session_state.usage_log = []
