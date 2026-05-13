"""
pipeline_engine.py
==================
Core engine for the Smart Pipeline Studio.

Phases:
  1. PLAN   — LLM generates a structured multi-step execution plan from a goal
  2. MODIFY — user can add/remove/reorder/edit steps before running
  3. EXECUTE — steps run sequentially; each step's output feeds the next
  4. THOUGHT — each step optionally exposes chain-of-thought reasoning

The engine is provider-agnostic: pass any call_llm function.
"""

from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PipelineStep:
    index: int
    agent: str
    agent_icon: str
    instruction: str
    provider: str
    model: str
    status: str = "pending"      # pending | running | done | error | skipped
    output: str = ""
    thought: str = ""
    reading: list[str] = field(default_factory=list)
    elapsed: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    error: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass
class PipelineRun:
    goal: str
    steps: list[PipelineStep]
    status: str = "idle"         # idle | planning | planned | running | done | error
    started_at: str = ""
    finished_at: str = ""
    total_elapsed: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# THOUGHT parsing
# ─────────────────────────────────────────────────────────────────────────────
THOUGHT_SYSTEM = """\
You are an expert AI agent. Before giving your response, ALWAYS expose your reasoning using this EXACT XML structure:

<thinking>
Step 1: [what you are reading / analyzing]
Step 2: [what you infer]
Step 3: [what you will do and why]
</thinking>

<reading>
• [item you are referencing]
• [another item]
</reading>

<answer>
[Your actual response / output]
</answer>

Never skip <thinking> or <reading>. Be thorough in your reasoning."""


def _wrap_with_thought_prompt(instruction: str, context: str) -> str:
    parts = [f"Previous pipeline context:\n{context}\n\n"] if context.strip() else []
    parts.append(instruction)
    return "\n".join(parts)


def parse_thought_response(raw: str) -> dict:
    """Parse <thinking>, <reading>, <answer> blocks from raw LLM output."""
    def extract(tag: str) -> str:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    thinking = extract("thinking")
    reading_raw = extract("reading")
    answer = extract("answer")

    reading_items = [
        line.lstrip("•- ").strip()
        for line in reading_raw.splitlines()
        if line.strip() and line.strip() not in ("•", "-")
    ] if reading_raw else []

    # If no XML found, the entire response is the answer
    if not thinking and not answer:
        answer = raw

    return {
        "thinking": thinking,
        "reading": reading_items,
        "answer": answer or raw,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PLANNER
# ─────────────────────────────────────────────────────────────────────────────
PLAN_SYSTEM = """\
You are a pipeline architect. Given a goal and a list of available agents, design an optimal multi-step pipeline.

Return ONLY a JSON array (no markdown, no explanation) of steps:
[
  {
    "agent": "<agent_id from available list>",
    "instruction": "<what this step should do, referencing the previous step's output where relevant>",
    "reason": "<one sentence why this step is needed>"
  },
  ...
]

Rules:
- Use 2–6 steps. Never more than 8.
- Each step must reference what the previous step produced.
- Instructions must be specific and actionable.
- Use the exact agent_id strings from the available agents list."""


def build_plan(
    goal: str,
    available_agents: dict,
    call_llm: Callable,
    provider: str,
    model: str,
    api_key: str,
) -> list[dict] | None:
    """
    Ask the LLM to generate a pipeline plan for `goal`.
    Returns list of step dicts or None on failure.
    """
    agents_desc = "\n".join(
        f'  - {aid}: {a["name"]} — {a["description"]}'
        for aid, a in available_agents.items()
    )
    user_msg = f"""Goal: {goal}

Available agents:
{agents_desc}

Design the best pipeline to achieve this goal."""

    result = call_llm(
        provider_id=provider,
        model=model,
        messages=[{"role": "user", "content": user_msg}],
        api_key=api_key,
        system=PLAN_SYSTEM,
        max_tokens=1500,
        temperature=0.4,
    )

    if result.get("error"):
        return None

    raw = result["text"].strip()
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")

    try:
        plan = json.loads(raw)
        if isinstance(plan, list):
            return plan
    except json.JSONDecodeError:
        # Try to extract JSON array from within text
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────
def execute_pipeline(
    run: PipelineRun,
    call_llm: Callable,
    api_keys: dict,
    agents: dict,
    *,
    thought_mode: bool = True,
    on_step_start: Callable | None = None,
    on_step_done: Callable | None = None,
    is_interrupted: Callable | None = None,
) -> PipelineRun:
    """
    Execute all steps in `run` sequentially.
    Updates each step in-place with output, thought, status, timing.

    Callbacks:
      on_step_start(step_index)
      on_step_done(step)
      is_interrupted() -> bool
    """
    run.status = "running"
    run.started_at = datetime.now().strftime("%H:%M:%S")
    t_total = time.time()

    context_chain = []  # accumulated outputs for context injection

    for step in run.steps:
        if is_interrupted and is_interrupted():
            step.status = "skipped"
            continue

        if step.status == "skipped":
            continue

        step.status = "running"
        step.started_at = datetime.now().strftime("%H:%M:%S")

        if on_step_start:
            on_step_start(step.index)

        # Build context from previous outputs
        context = "\n\n---\n\n".join(
            f"Step {i+1} output:\n{out}" for i, out in enumerate(context_chain)
        )

        agent = agents.get(step.agent, {})
        system_prompt = agent.get("system_prompt", "You are a helpful AI assistant.")

        if thought_mode:
            full_system = system_prompt + "\n\n" + THOUGHT_SYSTEM
        else:
            full_system = system_prompt

        user_content = _wrap_with_thought_prompt(step.instruction, context)

        t0 = time.time()
        api_key = api_keys.get(step.provider, "")
        result = call_llm(
            provider_id=step.provider,
            model=step.model,
            messages=[{"role": "user", "content": user_content}],
            api_key=api_key,
            system=full_system,
            max_tokens=2048,
            temperature=0.5,
        )
        step.elapsed = round(time.time() - t0, 2)
        step.finished_at = datetime.now().strftime("%H:%M:%S")

        if result.get("error"):
            step.status = "error"
            step.error = result["error"]
            step.output = f"[Error] {result['error']}"
            context_chain.append(f"[Step {step.index} failed: {result['error']}]")
        else:
            raw = result["text"]
            if thought_mode:
                parsed = parse_thought_response(raw)
                step.thought = parsed["thinking"]
                step.reading = parsed["reading"]
                step.output = parsed["answer"]
            else:
                step.output = raw

            step.status = "done"
            step.tokens_in = result.get("input_tokens", 0)
            step.tokens_out = result.get("output_tokens", 0)
            context_chain.append(step.output)

        if on_step_done:
            on_step_done(step)

    run.total_elapsed = round(time.time() - t_total, 2)
    run.finished_at = datetime.now().strftime("%H:%M:%S")
    all_done = all(s.status in ("done", "skipped") for s in run.steps)
    run.status = "done" if all_done else "error"
    return run


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def steps_from_plan(
    plan: list[dict],
    agents: dict,
    default_provider: str,
    default_model: str,
) -> list[PipelineStep]:
    """Convert a raw plan list into PipelineStep objects."""
    steps = []
    for i, item in enumerate(plan):
        agent_id = item.get("agent", "")
        agent = agents.get(agent_id, {})
        steps.append(
            PipelineStep(
                index=i + 1,
                agent=agent_id,
                agent_icon=agent.get("icon", "🤖"),
                instruction=item.get("instruction", ""),
                provider=default_provider,
                model=default_model,
            )
        )
    return steps


def run_summary(run: PipelineRun) -> dict:
    total_in = sum(s.tokens_in for s in run.steps)
    total_out = sum(s.tokens_out for s in run.steps)
    done = sum(1 for s in run.steps if s.status == "done")
    errors = sum(1 for s in run.steps if s.status == "error")
    return {
        "steps_total": len(run.steps),
        "steps_done": done,
        "steps_error": errors,
        "tokens_in": total_in,
        "tokens_out": total_out,
        "elapsed": run.total_elapsed,
    }
