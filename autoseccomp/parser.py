import re
from typing import Set, Iterable

_SYSCALL_RE = re.compile(r'^\s*[0-9]+(?:\s+[0-9.]+)?\s+([a-zA-Z0-9_]+)\(')

def iter_syscalls(lines: Iterable[str]) -> Iterable[str]:
    """Yield syscall names found at start of each strace line."""
    for line in lines:
        m = _SYSCALL_RE.match(line)
        if m:
            yield m.group(1)

def parse_strace(path: str) -> Set[str]:
    """Return a set of unique syscalls detected in a strace -f log."""
    with open(path, 'r', errors='ignore') as fh:
        return set(iter_syscalls(fh))
