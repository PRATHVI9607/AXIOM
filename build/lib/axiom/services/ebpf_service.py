"""eBPF runtime tracer client (PRD §7.3).

The actual kernel probing happens in a SEPARATE privileged daemon
(`axiom.workers.ebpf_worker`) running in WSL/Linux (Critical Rule #2). This
service is a thin async CLIENT that pulls captured RuntimeEvents from that
daemon over localhost and aggregates per-function feature counts for the GNN.

If the daemon is unreachable (not started, no WSL, no capabilities) the service
reports unavailable and returns zeroed features so the platform keeps running in
static-only mode (Critical Rule #7) — a required safety net, not the happy path.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from axiom.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class RuntimeEvent:
    """A single captured kernel event (PRD §7.3 data structure)."""

    event_type: str
    pid: int
    tid: int
    timestamp_ns: int
    comm: str = ""
    arg: str = ""
    function_stack: list[str] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)
    resolved_function_id: str | None = None


class EbpfTracerClient:
    """Connects to the WSL tracer daemon and exposes recent runtime events."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._last_ok = False

    @property
    def enabled(self) -> bool:
        return self.settings.ebpf_enabled

    async def fetch_events(self, timeout: float = 2.0) -> list[RuntimeEvent]:
        """Pull the tracer's current ring buffer. Returns [] if daemon is down."""
        if not self.enabled:
            return []
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.settings.ebpf_tracer_host, self.settings.ebpf_tracer_port
                ),
                timeout=timeout,
            )
            data = await asyncio.wait_for(reader.readline(), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            payload = json.loads(data.decode())
            self._last_ok = True
            return [self._to_event(e) for e in payload.get("events", [])]
        except (OSError, asyncio.TimeoutError, json.JSONDecodeError) as exc:
            if self._last_ok:  # only log the transition to down, avoid spam
                logger.warning("eBPF tracer unreachable, static-only mode: %s", exc)
            self._last_ok = False
            return []

    async def is_available(self) -> bool:
        """True if the tracer daemon actually answered recently."""
        events = await self.fetch_events()
        return self._last_ok

    @staticmethod
    def _to_event(raw: dict[str, Any]) -> RuntimeEvent:
        return RuntimeEvent(
            event_type=raw.get("event_type", "unknown"),
            pid=int(raw.get("pid", 0)),
            tid=int(raw.get("tid", 0)),
            timestamp_ns=int(raw.get("timestamp_ns", 0)),
            comm=raw.get("comm", ""),
            arg=raw.get("arg", ""),
        )

    async def summarize(self) -> dict[str, dict[str, Any]]:
        """Aggregate live events into per-command runtime feature counts.

        Keyed by process `comm`; the analysis worker maps these onto function IDs
        once PID→function resolution (DWARF, Phase 1C) is wired in.
        """
        events = await self.fetch_events()
        summary: dict[str, dict[str, Any]] = {}
        for e in events:
            bucket = summary.setdefault(
                e.comm,
                {
                    "syscall_count": 0,
                    "file_access_count": 0,
                    "net_connect_count": 0,
                    "spawn_count": 0,
                    "priv_esc_count": 0,
                    "top_paths": [],
                },
            )
            bucket["syscall_count"] += 1
            if e.event_type == "file_open":
                bucket["file_access_count"] += 1
                if e.arg and e.arg not in bucket["top_paths"] and len(bucket["top_paths"]) < 5:
                    bucket["top_paths"].append(e.arg)
            elif e.event_type == "net_connect":
                bucket["net_connect_count"] += 1
            elif e.event_type == "process_spawn":
                bucket["spawn_count"] += 1
            elif e.event_type == "privilege":
                bucket["priv_esc_count"] += 1
        return summary


_client: EbpfTracerClient | None = None


def get_tracer() -> EbpfTracerClient:
    global _client
    if _client is None:
        _client = EbpfTracerClient()
    return _client
