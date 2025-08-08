# AutoSeccomp‑Gen

Generate a ready‑to‑ship seccomp profile from **one single run** of your program or container.

<p align="center">
  <img width="500" src="docs/demo.gif" alt="asciinema demo">
</p>

## Why

- **Smaller attack surface** – only the syscalls you actually need stay open.
- **Zero manual editing** – no more scrolling through huge strace logs.
- **Works everywhere** – plain Python 3, strace and Docker; ARM64 & x86‑64.

## Quick start

```bash
pip install -r requirements.txt
# list the network‑free syscalls of /bin/ls
autoseccomp trace-run "/bin/ls /" -o ls.json
# try to ping with that profile → blocked
docker run --rm --security-opt seccomp=ls.json busybox ping -c1 8.8.8.8

CLI
Sub‑command	Description
trace <log>	Show unique syscalls from an existing strace -f file.
generate <log> -o profile.json	Build a seccomp profile from that trace.
trace-run "<cmd>" -o profile.json	All‑in‑one: trace, generate, validate.

How it works
Runs your command under strace -f.

Merges the detected syscalls with a minimal Docker baseline (no networking).

Writes seccomp.json and re‑runs the command inside BusyBox to prove it works.

