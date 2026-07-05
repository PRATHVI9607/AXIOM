#!/usr/bin/env bash
# setup_ebpf_wsl.sh — install BCC + kernel headers so the AXIOM eBPF tracer runs
# inside WSL2 (Ubuntu). Run this ONCE inside WSL:  bash scripts/setup_ebpf_wsl.sh
set -euo pipefail

echo "==> AXIOM eBPF setup for WSL2"
KERNEL="$(uname -r)"
echo "    Kernel: ${KERNEL}"

if ! grep -qi microsoft /proc/version; then
    echo "!!  This does not look like WSL. The tracer needs a Linux kernel."
fi

echo "==> Installing BCC toolchain (needs sudo)…"
sudo apt-get update
sudo apt-get install -y \
    bpfcc-tools python3-bpfcc libbpfcc \
    linux-headers-generic build-essential python3-pip

# WSL kernels ship headers under /usr/lib/modules; BCC expects them discoverable.
if [ ! -d "/usr/src/linux-headers-${KERNEL}" ] && [ ! -d "/lib/modules/${KERNEL}/build" ]; then
    echo "!!  Headers for ${KERNEL} not found. If BCC fails to compile, install the"
    echo "    WSL2 kernel headers matching your kernel, or run a custom WSL2 kernel."
fi

echo "==> Verifying BCC can load a probe (quick smoke test)…"
sudo python3 - <<'PY'
try:
    from bcc import BPF
    b = BPF(text=r'''
        int hello(void *ctx) { return 0; }
    ''')
    print("    OK: BCC compiled and loaded a trivial program.")
except Exception as e:  # noqa
    print(f"    WARN: BCC smoke test failed: {e}")
PY

echo
echo "==> Done. Start the tracer with:"
echo "    cd \$(wslpath 'c:\\Workspace\\AXIOM') && sudo python3 -m axiom.workers.ebpf_worker --port 8770"
echo "    The API (Windows or WSL) reaches it at 127.0.0.1:8770 automatically."
