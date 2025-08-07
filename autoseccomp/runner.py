import shlex, subprocess, tempfile, uuid, sys
from pathlib import Path
from rich import print

from autoseccomp.parser import parse_strace
from autoseccomp.generator import build_profile, save_profile


def _run(cmd, **kw):
    """Wrapper around subprocess.run that captures stdout/stderr."""
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------------------

def trace_run(cmd: str, out: Path) -> None:
    """Trace → build profile → validate inside BusyBox (all‑in‑one)."""
    with tempfile.TemporaryDirectory() as td:
        trace_file = Path(td) / "trace.log"

        print(f"[cyan]⏱  Tracing:[/] {cmd}")
        rc = _run(["strace", "-f", "-qq", "-o", trace_file, *shlex.split(cmd)]).returncode
        if rc:
            print(f"[red]❌  Command exited with status {rc}; aborting.[/red]")
            sys.exit(rc)

        profile = build_profile(parse_strace(trace_file))
        save_profile(profile, out)
        print(f"[cyan]📄  Profile written →[/] {out}")

    _validate(out, cmd)


def _validate(profile_path: Path, cmd: str) -> None:
    """Run the command inside BusyBox using the freshly created profile."""
    print("[cyan]🔄  Validating inside BusyBox…[/]")
    cname = f"as-{uuid.uuid4().hex[:8]}"

    rc = _run([
        "docker", "run", "--rm", "--name", cname,
        "--security-opt", f"seccomp={profile_path.resolve()}",
        "busybox", "sh", "-c", cmd
    ]).returncode

    if rc == 0:
        print("[green]✔  Validation OK – no syscalls blocked[/]")
    else:
        print(f"[red]✖  Validation failed – container exit code {rc}[/red]")
