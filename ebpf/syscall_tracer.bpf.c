// syscall_tracer.bpf.c — BCC eBPF program that captures security-relevant syscalls.
// Loaded at runtime by axiom/workers/ebpf_worker.py via bcc.BPF(text=...).
// Uses stable syscall tracepoints (arch-independent) and a perf ring buffer.

#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

#define ARG_LEN 128

// Event categories mirrored in RuntimeEvent.event_type on the Python side.
enum evt_type {
    EVT_FILE_OPEN = 1,
    EVT_NET_CONNECT = 2,
    EVT_PROC_EXEC = 3,
    EVT_PRIVILEGE = 4,
};

struct data_t {
    u32 pid;
    u32 tid;
    u32 uid;
    u64 ts_ns;
    u32 etype;
    char comm[TASK_COMM_LEN];
    char arg[ARG_LEN];   // path / target / argv0 depending on etype
};

BPF_PERF_OUTPUT(events);

static __always_inline void fill_common(struct data_t *d, u32 etype) {
    u64 id = bpf_get_current_pid_tgid();
    d->pid = id >> 32;
    d->tid = (u32)id;
    d->uid = bpf_get_current_uid_gid() & 0xffffffff;
    d->ts_ns = bpf_ktime_get_ns();
    d->etype = etype;
    bpf_get_current_comm(&d->comm, sizeof(d->comm));
}

// File opens — sys_enter_openat carries the pathname pointer.
TRACEPOINT_PROBE(syscalls, sys_enter_openat) {
    struct data_t data = {};
    fill_common(&data, EVT_FILE_OPEN);
    bpf_probe_read_user_str(&data.arg, sizeof(data.arg), (void *)args->filename);
    events.perf_submit(args, &data, sizeof(data));
    return 0;
}

// Process exec — capture the program path.
TRACEPOINT_PROBE(syscalls, sys_enter_execve) {
    struct data_t data = {};
    fill_common(&data, EVT_PROC_EXEC);
    bpf_probe_read_user_str(&data.arg, sizeof(data.arg), (void *)args->filename);
    events.perf_submit(args, &data, sizeof(data));
    return 0;
}

// Network connect — record that a connect happened (address parsed in userspace).
TRACEPOINT_PROBE(syscalls, sys_enter_connect) {
    struct data_t data = {};
    fill_common(&data, EVT_NET_CONNECT);
    __builtin_memcpy(&data.arg, "connect", 8);
    events.perf_submit(args, &data, sizeof(data));
    return 0;
}

// Privilege change — setuid is a strong signal for the GNN's priv_esc feature.
TRACEPOINT_PROBE(syscalls, sys_enter_setuid) {
    struct data_t data = {};
    fill_common(&data, EVT_PRIVILEGE);
    __builtin_memcpy(&data.arg, "setuid", 7);
    events.perf_submit(args, &data, sizeof(data));
    return 0;
}
