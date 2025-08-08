import os, shlex, subprocess, tempfile, uuid, sys
from pathlib import Path
from rich import print

from autoseccomp.parser import parse_strace
from autoseccomp.generator import build_profile, save_profile


def _run(cmd):
    """Run command and capture stdout/stderr."""
    return subprocess.run(cmd, capture_output=True, text=True)


def trace_run(cmd: str, out: Path) -> None:
    """Trace → build profile → validate inside BusyBox."""
    with tempfile.TemporaryDirectory() as td:
        trace_file = Path(td) / "trace.log"
        print(f"[cyan]⏱  Tracing:[/] {cmd}")
        rc = _run(["strace", "-f", "-qq", "-o", str(trace_file), *shlex.split(cmd)]).returncode
        if rc:
            print(f"[red]❌  Command exited with status {rc}; aborting.[/red]")
            sys.exit(rc)

        profile = build_profile(parse_strace(trace_file))
        save_profile(profile, out)
        print(f"[cyan]📄  Profile written →[/] {out}")

    _validate(out, cmd)


def _validate(profile_path: Path, cmd: str) -> None:
    """Run the command inside BusyBox using the generated profile."""
    print("[cyan]🔄  Validating inside BusyBox…[/]")
    cname = f"as-{uuid.uuid4().hex[:8]}"

    # Allow overriding the command used for validation to avoid flaky networking.
    validate_cmd = os.environ.get("AUTOSECCOMP_VALIDATE_CMD", cmd)

    docker_cmd = [
        "docker", "run", "--rm", "--name", cname,
        "--security-opt", f"seccomp={profile_path.resolve()}",
        "busybox", "sh", "-c", validate_cmd
    ]
    res = _run(docker_cmd)
    rc = res.returncode

    if rc == 0:
        print("[green]✔  Validation OK – no syscalls blocked[/]")
    else:
        msg = (res.stderr or "") + "\n" + (res.stdout or "")
        # Heuristic to distinguish seccomp denial from app/network failure
        if "Operation not permitted" in msg or "seccomp" in msg.lower():
            print(f"[red]✖  Validation failed – likely blocked by seccomp (rc={rc})[/red]")
        else:
            print(f"[yellow]⚠  Container exited with rc={rc}, likely not a seccomp denial (e.g., DNS/network).[/yellow]")
