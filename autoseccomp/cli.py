import argparse
from rich import print
from rich.table import Table

from autoseccomp.parser import parse_strace

def cmd_trace(path: str):
    syscalls = sorted(parse_strace(path))
    table = Table(title=f"Syscalls in {path}", show_lines=True)
    table.add_column("Count", justify="right")
    table.add_column("Syscall")

    for i, sc in enumerate(syscalls, 1):
        table.add_row(str(i), sc)

    print(table)
    print(f"[bold green]Total unique syscalls:[/] {len(syscalls)}")

def main():
    parser = argparse.ArgumentParser(
        prog="autoseccomp", description="AutoSeccomp-Gen CLI (step 2)")
    parser.add_argument(
        "--trace", metavar="FILE",
        help="Parse an existing strace -f log and list unique syscalls")

    args = parser.parse_args()

    if args.trace:
        cmd_trace(args.trace)
    else:
        print("[bold yellow]No option provided. Use --trace FILE.[/]")

if __name__ == '__main__':
    main()
