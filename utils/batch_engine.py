"""
batch_engine.py — helpers for the Batch Runner page.
"""

from __future__ import annotations
import csv
import io
from dataclasses import dataclass, field
from typing import Optional

from utils.cost_engine import MODEL_PRICING


@dataclass
class BatchResult:
    index: int
    input_text: str
    output_text: str
    input_tokens: int
    output_tokens: int
    elapsed: float
    timestamp: str
    error: Optional[str] = None


def estimate_batch_cost(
    template: str,
    inputs: list[str],
    model: str,
    max_output_tokens: int,
) -> dict:
    """
    Rough pre-run cost estimate.
    Uses 4 chars ≈ 1 token as a simple heuristic.
    """
    if not inputs:
        return {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

    avg_input_len = sum(len(template) + len(i) for i in inputs) / len(inputs)
    total_input_tokens = int(avg_input_len / 4) * len(inputs)
    total_output_tokens = max_output_tokens * len(inputs)

    pricing = MODEL_PRICING.get(model, {"input": 3.0, "output": 15.0})
    cost = (
        total_input_tokens  / 1_000_000 * pricing["input"] +
        total_output_tokens / 1_000_000 * pricing["output"]
    )
    return {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cost": cost,
    }


def run_batch_sync(
    client,
    template: str,
    inputs: list[str],
    model: str,
    max_tokens: int,
    temperature: float,
) -> list[BatchResult]:
    """
    Synchronously run the template against each input.
    Returns a list of BatchResult objects.
    Caller controls the client object (anthropic.Anthropic).
    """
    import time
    from datetime import datetime

    results = []
    for idx, inp in enumerate(inputs):
        filled = template
        for placeholder in ["{{input}}", "{{text}}", "{{content}}"]:
            filled = filled.replace(placeholder, inp)

        start = time.time()
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": filled}],
            )
            output = resp.content[0].text
            in_tok = resp.usage.input_tokens
            out_tok = resp.usage.output_tokens
            err = None
        except Exception as e:
            output = ""
            in_tok = out_tok = 0
            err = str(e)

        results.append(
            BatchResult(
                index=idx + 1,
                input_text=inp,
                output_text=output,
                input_tokens=in_tok,
                output_tokens=out_tok,
                elapsed=round(time.time() - start, 2),
                timestamp=datetime.now().strftime("%H:%M:%S"),
                error=err,
            )
        )
    return results


def results_to_csv(results: list[BatchResult]) -> str:
    """Serialize batch results to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "index", "timestamp", "input_text", "output_text",
        "input_tokens", "output_tokens", "elapsed_s", "error",
    ])
    for r in results:
        writer.writerow([
            r.index, r.timestamp, r.input_text, r.output_text,
            r.input_tokens, r.output_tokens, r.elapsed,
            r.error or "",
        ])
    return buf.getvalue()
