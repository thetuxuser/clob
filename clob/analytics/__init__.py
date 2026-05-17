"""Token and cost analytics for clob.

Tracks:
- Input/output tokens per session
- Estimated cost based on provider pricing
- Daily/session usage summaries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# ── Provider pricing (per 1M tokens, USD) ─────────────────────

PRICING: dict[str, dict[str, float]] = {
    # provider -> model_prefix -> (input, output) per 1M tokens
    "openrouter": {
        "default": (0.50, 1.50),
        "openai/gpt-4o": (2.50, 10.00),
        "openai/gpt-4o-mini": (0.15, 0.60),
        "anthropic/claude": (3.00, 15.00),
        "meta-llama": (0.05, 0.05),
    },
    "groq": {
        "default": (0.05, 0.10),
        "llama3-70b": (0.59, 0.79),
        "llama3-8b": (0.05, 0.08),
        "mixtral": (0.24, 0.24),
    },
    "ollama": {
        "default": (0.0, 0.0),  # local, free
    },
    "nvidia": {
        "default": (0.20, 0.20),
    },
}


def _estimate_cost(provider: str, model: str, in_tokens: int, out_tokens: int) -> float:
    """Estimate USD cost for a completion."""
    provider_prices = PRICING.get(provider, PRICING.get("openrouter", {}))

    # Find best matching model prefix
    in_price, out_price = provider_prices.get("default", (0.50, 1.50))
    for prefix, prices in provider_prices.items():
        if prefix != "default" and model.startswith(prefix):
            in_price, out_price = prices
            break

    return (in_tokens * in_price + out_tokens * out_price) / 1_000_000


@dataclass
class TurnStats:
    """Stats for a single request/response turn."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: __import__("datetime").datetime.now())

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        return _estimate_cost(self.provider, self.model, self.input_tokens, self.output_tokens)


@dataclass
class SessionStats:
    """Aggregated stats for a session."""

    session_id: int
    turns: list[TurnStats] = field(default_factory=list)

    def record(self, turn: TurnStats) -> None:
        self.turns.append(turn)

    @property
    def total_input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.turns)

    @property
    def total_output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.turns)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        return sum(t.estimated_cost_usd for t in self.turns)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def summary_line(self) -> str:
        """One-line summary for status bar."""
        cost = self.total_cost_usd
        cost_str = f"${cost:.4f}" if cost > 0 else "free"
        return f"↑{self.total_input_tokens} ↓{self.total_output_tokens} {cost_str}"


class AnalyticsTracker:
    """Runtime analytics tracker — in-memory for current session."""

    def __init__(self) -> None:
        self._sessions: dict[int, SessionStats] = {}
        self._global_turns: list[TurnStats] = []

    def record(self, session_id: int, turn: TurnStats) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionStats(session_id=session_id)
        self._sessions[session_id].record(turn)
        self._global_turns.append(turn)

    def get_session(self, session_id: int) -> SessionStats | None:
        return self._sessions.get(session_id)

    def global_summary(self) -> dict:
        total_in = sum(t.input_tokens for t in self._global_turns)
        total_out = sum(t.output_tokens for t in self._global_turns)
        total_cost = sum(t.estimated_cost_usd for t in self._global_turns)
        return {
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_tokens": total_in + total_out,
            "total_cost_usd": total_cost,
            "turn_count": len(self._global_turns),
        }

    def format_usage_report(self) -> str:
        g = self.global_summary()
        lines = [
            "── clob Usage Report ────────────────────────",
            f"  Total turns:    {g['turn_count']}",
            f"  Input tokens:   {g['total_input_tokens']:,}",
            f"  Output tokens:  {g['total_output_tokens']:,}",
            f"  Total tokens:   {g['total_tokens']:,}",
            f"  Est. cost:      ${g['total_cost_usd']:.4f} USD",
            "─────────────────────────────────────────────",
        ]
        return "\n".join(lines)
