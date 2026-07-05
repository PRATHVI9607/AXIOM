"""Privileged eBPF tracer daemon — runs INSIDE WSL/Linux as root (PRD §7.3).

Loads ebpf/syscall_tracer.bpf.c via BCC, polls the perf ring buffer, and serves
recent RuntimeEvents as newline-delimited JSON over a localhost TCP socket that
the (possibly Windows-side) API reads. This is a SEPARATE process from the API
(Critical Rule #2) — never import it into the FastAPI event loop.

Run it in WSL:
    sudo python3 -m axiom.workers.ebpf_worker --port 8770
"""
from __future__ import annotations

import argparse
import json
import logging
import socket
import threading
import time
from collections import deque
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ebpf] %(message)s")
logger = logging.getLogger(__name__)

BPF_SOURCE = Path(__file__).resolve().parent.parent.parent / "ebpf" / "syscall_tracer.bpf.c"

ETYPE_NAMES = {1: "file_open", 2: "net_connect", 3: "process_spawn", 4: "privilege"}


class RingBuffer:
    """Thread-safe fixed-size event ring (oldest dropped when full, per PRD §7.3)."""

    def __init__(self, maxlen: int = 10_000) -> None:
        self._events: deque[dict] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def push(self, event: dict) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self, limit: int = 1000) -> list[dict]:
        with self._lock:
            return list(self._events)[-limit:]


def build_bpf():
    """Compile and load the eBPF program. Requires bcc + root + Linux."""
    from bcc import BPF  # imported lazily so the module is importable anywhere

    text = BPF_SOURCE.read_text(encoding="utf-8")
    logger.info("Compiling eBPF program from %s", BPF_SOURCE.name)
    return BPF(text=text)


def run_tracer(port: int) -> None:
    """Main daemon loop: attach probes, stream perf events into the ring buffer."""
    ring = RingBuffer()
    bpf = build_bpf()

    def handle_event(cpu, data, size):  # noqa: ARG001 - BCC callback signature
        event = bpf["events"].event(data)
        ring.push(
            {
                "event_type": ETYPE_NAMES.get(event.etype, "unknown"),
                "pid": event.pid,
                "tid": event.tid,
                "uid": event.uid,
                "timestamp_ns": event.ts_ns,
                "comm": event.comm.decode("utf-8", "replace"),
                "arg": event.arg.decode("utf-8", "replace"),
            }
        )

    bpf["events"].open_perf_buffer(handle_event, page_cnt=64)
    _start_socket_server(port, ring)
    logger.info("Tracer running. Serving events on 127.0.0.1:%d (Ctrl-C to stop).", port)

    try:
        while True:
            bpf.perf_buffer_poll(timeout=100)
    except KeyboardInterrupt:
        logger.info("Shutting down tracer.")


def _start_socket_server(port: int, ring: RingBuffer) -> None:
    """Serve the current ring buffer as JSON to any client that connects."""

    def serve() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(8)
        while True:
            conn, _ = srv.accept()
            with conn:
                payload = json.dumps({"events": ring.snapshot()}).encode() + b"\n"
                try:
                    conn.sendall(payload)
                except OSError as exc:
                    logger.warning("Client send failed: %s", exc)

    threading.Thread(target=serve, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="AXIOM eBPF tracer daemon (Linux/WSL, root)")
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    try:
        run_tracer(args.port)
    except ImportError:
        logger.error("bcc not installed. In WSL run: scripts/setup_ebpf_wsl.sh")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Tracer failed (need root? run with sudo): %s", exc)
        raise


if __name__ == "__main__":
    main()
