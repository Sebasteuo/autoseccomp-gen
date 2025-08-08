import json
from pathlib import Path
from typing import Iterable, Dict, Set

# ------------------------------------------------------------------ helpers
def _load_docker_allowlist() -> Set[str]:
    """Return the set of SCMP_ACT_ALLOW syscalls from Docker's default profile, if present."""
    candidates = [
        Path("/usr/share/docker/seccomp.json"),
        Path("/usr/share/containers/oci/seccomp.json"),
    ]
    for p in candidates:
        if p.exists():
            data = json.loads(p.read_text())
            names: Set[str] = set()
            for entry in data.get("syscalls", []):
                if entry.get("action") == "SCMP_ACT_ALLOW":
                    names.update(entry.get("names", []))
            return names
    return set()  # fall back provided below


DOCKER_DEFAULT: Set[str] = _load_docker_allowlist()

# Syscalls we must force-allow because modern runc/Go frequently require them
MUST_HAVE: Set[str] = {
    # synchronization / Go runtime / runc
    "futex", "futex_time64", "futex_waitv",
    # open with modern resolution semantics
    "openat2",
    # fs stats on FDs (used to verify procfs)
    "fstatfs",
    # modern helpers commonly used
    "statx", "close_range",
    # common metadata ops
    "newfstatat", "readlinkat",
    # runc/cred mgmt
    "capget", "capset", "prctl",
    "set_tid_address", "set_robust_list", "prlimit64", "sched_yield", "rseq",
}

# Robust fallback (covers runc/libcontainer init + common userspace)
if not DOCKER_DEFAULT:
    DOCKER_DEFAULT = {
        # process / memory / signals
        "brk","clone","clone3","close","close_range",
        "execve","exit_group","fstat","newfstatat","statx","statfs","fstatfs",
        "getdents64","getpid","getppid","getuid","getgid","geteuid","getegid",
        "set_tid_address","set_robust_list","mmap","mprotect","munmap",
        "prctl","rt_sigaction","rt_sigprocmask","rt_sigreturn","sigaltstack",
        "setrlimit","read","write","lseek","sched_yield","rseq",
        # synchronization
        "futex","futex_time64","futex_waitv",
        # file-system
        "open","openat","openat2","fcntl","ioctl","getrandom","faccessat",
        "readlink","readlinkat","chmod","fchmod","fchmodat","linkat",
        "unlinkat","renameat2","utimensat","ftruncate",
        # epoll/event (safe set)
        "epoll_create1","epoll_ctl","epoll_pwait","epoll_wait","eventfd2",
        # namespaces / misc
        "chdir","getcwd","setns","umask",
        # credentials / limits / caps
        "setuid","setuid32","setgid","setgid32",
        "setresuid","setresgid","setfsuid","setfsuid32","setfsgid","setfsgid32",
        "setgroups","setgroups32","getgroups","getgroups32",
        "capget","capset",
        "prlimit64",
        # pidfd helpers (harmless if absent)
        "pidfd_open","pidfd_getfd","pidfd_send_signal",
        # timers
        "timerfd_create","timerfd_settime","timerfd_gettime",
    }
else:
    # Ensure required modern syscalls are present even if Docker's file is older
    DOCKER_DEFAULT |= MUST_HAVE

# Remove networking from the baseline (start "no‑net" by default)
NET_SYSCALLS = {
    "socket","socketpair","bind","connect","accept","accept4","listen",
    "getsockname","getpeername","sendto","recvfrom","sendmsg","recvmsg",
    "shutdown","setsockopt","getsockopt",
}
BASELINE = DOCKER_DEFAULT - NET_SYSCALLS

ARCH_MAP = [
    {"architecture": "SCMP_ARCH_AARCH64", "subArchitectures": []},
    {"architecture": "SCMP_ARCH_X86_64",  "subArchitectures": []},
]

# ------------------------------------------------------------------ API
def build_profile(trace_syscalls: Iterable[str]) -> Dict:
    allowed = sorted(set(trace_syscalls) | BASELINE)
    return {
        "defaultAction": "SCMP_ACT_ERRNO",
        "archMap": ARCH_MAP,
        "syscalls": [{
            "names": allowed,
            "action": "SCMP_ACT_ALLOW",
            "args": [],
            "comment": "AutoSeccomp-Gen (Docker default minus NET + trace + MUST_HAVE)",
            "includes": {},
            "excludes": {}
        }],
    }

def save_profile(profile: Dict, path: Path) -> None:
    path.write_text(json.dumps(profile, indent=2))
