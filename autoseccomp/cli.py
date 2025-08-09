#!/usr/bin/env python3
"""
AutoSeccomp-Gen CLI with simple ASCII banner and optional interactive menu.

Subcommands:
  - trace:     list syscalls from an existing strace log
  - generate:  generate a Seccomp profile from a strace log
  - trace-run: trace → profile → validate (BusyBox)
"""
import argparse
import os
import shutil
import time
from pathlib import Path

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from autoseccomp.parser import parse_strace
from autoseccomp.generator import build_profile, save_profile
from autoseccomp.runner import trace_run


# ------------------------------ Banner -------------------------------------
def _print_banner() -> None:
    """Print a simple ASCII boxed banner. Controlled by env vars:
       - AUTOSECCOMP_BANNER=0   -> disable banner
       - AUTOSECCOMP_AUTHOR=... -> author line
    """
    if os.getenv("AUTOSECCOMP_BANNER", "1") == "0":
        return
    title = "AutoSeccomp-Gen"
    subtitle = "Trace-driven Seccomp profiles for Docker"
    author = os.getenv("AUTOSECCOMP_AUTHOR", "").strip()

    lines = [title, subtitle]
    if author:
        lines.append(f"Author: {author}")

    width = max(len(s) for s in lines)
    top = "+" + "-" * (width + 2) + "+"
    print(top)
    for s in lines:
        print(f"| {s.ljust(width)} |")
    print(top)
    print()  # spacer


# ------------------------------ Helpers ------------------------------------
def _deps_table() -> Table:
    """Render a small dependency table."""
    deps = ("docker", "strace")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Dependency", justify="left")
    table.add_column("Status", justify="left")
    for d in deps:
        ok = shutil.which(d) is not None
        table.add_row(d, "[green]OK[/]" if ok else "[red]missing[/]")
    return table


def _interactive_main() -> None:
    """Minimal interactive UI."""
    _print_banner()

    # Little spinner just for a tiny bit of flair
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as prog:
        t = prog.add_task("Checking environment…", total=None)
        time.sleep(0.2)
        prog.update(t, description="Getting ready…")
        time.sleep(0.2)
        prog.stop()

    print(_deps_table())
    print(Panel.fit(
        "[bold]Welcome![/]\n"
        "Choose an action:\n"
        "  [1] Trace → Profile → Validate (recommended)\n"
        "  [2] Generate from strace log\n"
        "  [3] List syscalls from strace log\n"
        "  [Q] Quit",
        title="Menu", border_style="cyan"
    ))

    while True:
        choice = input("> ").strip().lower()
        if choice in ("q", "quit", "exit"):
            print("[cyan]Bye![/]")
            return
        elif choice in ("1", "trace-run"):
            cmd = input("Command to trace (e.g. /bin/ls /): ").strip()
            if not cmd:
                print("[red]A command is required.[/]")
                continue
            out = input("Output profile path [profile.json]: ").strip() or "profile.json"
            trace_run(cmd, Path(out))
            print(Panel.fit(f"Done. Profile → {out}", border_style="green"))
            break
        elif choice in ("2", "generate"):
            log = input("Path to strace log: ").strip()
            if not log:
                print("[red]A log path is required.[/]")
                continue
            out = input("Output profile path [profile.json]: ").strip() or "profile.json"
            syscalls = parse_strace(Path(log))
            profile = build_profile(syscalls)
            save_profile(profile, Path(out))
            print(Panel.fit(f"Done. Profile → {out}", border_style="green"))
            break
        elif choice in ("3", "trace"):
            log = input("Path to strace log: ").strip()
            if not log:
                print("[red]A log path is required.[/]")
                continue
            syscalls = parse_strace(Path(log))
            print(f"Total unique syscalls: {len(syscalls)}")
            for name in sorted(syscalls):
                print(f"- {name}")
            break
        else:
            print("[yellow]Invalid option. Try 1/2/3 or Q.[/]")


# ------------------------------ Commands -----------------------------------
def _cmd_trace(args: argparse.Namespace) -> None:
    """List syscalls found in a strace log."""
    syscalls = parse_strace(Path(args.log))
    _print_banner()
    print(f"Total unique syscalls: {len(syscalls)}")
    for name in sorted(syscalls):
        print(f"- {name}")


def _cmd_generate(args: argparse.Namespace) -> None:
    """Build and save a profile from a strace log."""
    _print_banner()
    syscalls = parse_strace(Path(args.log))
    profile = build_profile(syscalls)
    out = Path(args.out)
    save_profile(profile, out)
    print(f"Profile written -> {out}")


def _cmd_trace_run(args: argparse.Namespace) -> None:
    """Trace → profile → validate in BusyBox."""
    _print_banner()
    trace_run(args.cmd, Path(args.out))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="autoseccomp",
        description="AutoSeccomp‑Gen CLI",
    )
    parser.add_argument("--ui", action="store_true", help="launch interactive menu")

    # subparsers: not required so we can enter interactive mode if missing
    subs = parser.add_subparsers(dest="sub", required=False)

    # trace
    p_trace = subs.add_parser("trace", help="list syscalls from existing strace log")
    p_trace.add_argument("log", help="path to strace -o logfile")
    p_trace.set_defaults(func=_cmd_trace)

    # generate
    p_gen = subs.add_parser("generate", help="generate profile from strace log")
    p_gen.add_argument("log", help="path to strace -o logfile")
    p_gen.add_argument("-o", "--out", required=True, help="output JSON profile")
    p_gen.set_defaults(func=_cmd_generate)

    # trace-run
    p_tr = subs.add_parser("trace-run", help="trace → profile → validate (all‑in‑one)")
    p_tr.add_argument("cmd", help="shell-style command to trace (quote it)")
    p_tr.add_argument("-o", "--out", required=True, help="output JSON profile")
    p_tr.set_defaults(func=_cmd_trace_run)

    args = parser.parse_args()

    # If --ui or no subcommand, launch interactive menu
    if getattr(args, "ui", False) or args.sub is None:
        _interactive_main()
        return

    # Otherwise run the chosen subcommand (banner printed inside each)
    args.func(args)


if __name__ == "__main__":
    main()
