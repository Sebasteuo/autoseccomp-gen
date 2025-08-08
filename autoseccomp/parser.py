import re
from typing import Iterable, Set

_CALL_RE = re.compile(r'^\s*\d+(?:\s+\d+\.\d+)?\s+([a-zA-Z0-9_]+)\(')


def iter_syscalls(lines: Iterable[str]) -> Iterable[str]:
    """Yield every syscall found at the beginning of strace lines."""
    for line in lines:
        m = _CALL_RE.match(line)
        if m:
            yield m.group(1)


def parse_strace(path: str) -> Set[str]:
    """Return a *set* of unique syscalls found in a strace ‑f log."""
    with open(path, errors="ignore") as fh:
        return set(iter_syscalls(fh))

