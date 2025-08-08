import argparse
from pathlib import Path
from autoseccomp.parser import parse_strace
from autoseccomp.generator import build_profile, save_profile
from autoseccomp.runner import trace_run

def main() -> None:
    p = argparse.ArgumentParser(prog="autoseccomp", description="AutoSeccomp‑Gen CLI")
    sub = p.add_subparsers(dest="sub")

    s1 = sub.add_parser("trace", help="list syscalls from existing strace log")
    s1.add_argument("file")

    s2 = sub.add_parser("generate", help="generate profile from strace log")
    s2.add_argument("file")
    s2.add_argument("-o", "--out", default="seccomp.json")

    s3 = sub.add_parser("trace-run", help="trace → profile → validate (all‑in‑one)")
    s3.add_argument("cmd", help='command to run under strace (quote it)')
    s3.add_argument("-o", "--out", default="seccomp.auto.json")

    args = p.parse_args()

    if args.sub == "trace":
        syscalls = sorted(parse_strace(args.file))
        for i, sc in enumerate(syscalls, 1):
            print(f"{i:>3}. {sc}")
        print(f"Total unique: {len(syscalls)}")

    elif args.sub == "generate":
        prof = build_profile(parse_strace(args.file))
        save_profile(prof, Path(args.out))
        print(f"Profile written → {args.out}")

    elif args.sub == "trace-run":
        trace_run(args.cmd, Path(args.out))

    else:
        p.print_help()


if __name__ == "__main__":
    main()

