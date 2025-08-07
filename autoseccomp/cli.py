import argparse
from pathlib import Path
from rich import print
from rich.table import Table

from autoseccomp.parser import parse_strace
from autoseccomp.generator import build_profile, save_profile

def list_syscalls(path: str):
    syscalls = sorted(parse_strace(path))
    table = Table(title=f"Syscalls in {path}", show_lines=True)
    table.add_column("Count", justify="right")
    table.add_column("Syscall")
    for i, sc in enumerate(syscalls, 1):
        table.add_row(str(i), sc)
    print(table)
    print(f"[bold green]Total unique syscalls:[/] {len(syscalls)}")
    return syscalls

def main():
    p = argparse.ArgumentParser(
        prog="autoseccomp",
        description="AutoSeccomp-Gen (list syscalls or generate profile)")
    p.add_argument("--trace",   metavar="FILE", help="strace -f log to analyse")
    p.add_argument("--generate", action="store_true",
                   help="Generate seccomp.json next to TRACE file")
    args = p.parse_args()

    if args.trace:
        syscalls = list_syscalls(args.trace)
        if args.generate:
            out_path = Path(args.trace).with_suffix(".seccomp.json")
            profile = build_profile(syscalls)
            save_profile(profile, out_path)
            print(f"[bold cyan]Profile written → {out_path}[/]")
    else:
        p.print_help()

if __name__ == '__main__':
    main()
