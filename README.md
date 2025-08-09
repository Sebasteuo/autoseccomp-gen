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


## Screenshots

> A few real runs that show how AutoSeccomp‑Gen works end-to-end.

### 0) Preflight
- **Environment sanity checks**
  
  ![preflight](docs/screenshots/preflight.png)

---

### 1) No-network suite overview
- **One-shot view of the “no network” profile behavior**
  
  ![02-no-network-suite](docs/screenshots/02-no-network-suite.png)

---

### 2) Networking profile (HTTP)
- **S02A – Trace + validate “http.json”**  
  ![S02A_trace_http_profile_ok](docs/screenshots/S02A_trace_http_profile_ok.png)

- **S02B – Internet HTTP first line**  
  ![S02B_http_internet_first_line](docs/screenshots/S02B_http_internet_first_line.png)

- **S02C – Local network first line (nginx in isolated docker network)**  
  ![S02C_http_localnet_first_line](docs/screenshots/S02C_http_localnet_first_line.png)

- **S02D – http.json contains network syscalls (socket/connect/sendto/recvfrom)**  
  ![S02D_http_json_net_syscalls](docs/screenshots/S02D_http_json_net_syscalls.png)

---

### 3) No-network profile blocks local network
- **S03 – “ls.json” blocks HTTP even on the isolated docker network**  
  ![S03_ls_local_net_blocked](docs/screenshots/S03_ls_local_net_blocked.png)

---

### 4) Fork/wait scenario
- **S04A – Trace & validate**  
  ![S04A_fork_trace_validate_ok](docs/screenshots/S04A_fork_trace_validate_ok.png)

- **S04B – Run shows “OK”**  
  ![S04B_fork_run_ok](docs/screenshots/S04B_fork_run_ok.png)

- **S04C – fork.json has clone/wait syscalls**  
  ![S04C_fork_json_has_clone_wait](docs/screenshots/S04C_fork_json_has_clone_wait.png)

---

### 5) Basic I/O scenario
- **S05A – Trace & validate**  
  ![S05A_io_trace_validate_ok](docs/screenshots/S05A_io_trace_validate_ok.png)

- **S05B – Run prints “hi”**  
  ![S05B_io_run_hi](docs/screenshots/S05B_io_run_hi.png)

- **S05C – io.json includes expected FS syscalls**  
  ![S05C_io_json_has_fs_syscalls](docs/screenshots/S05C_io_json_has_fs_syscalls.png)

---

### 6) Mount is blocked (even with CAP_SYS_ADMIN)
- **S06A – mount blocked with no extra caps**  
  ![S06A_mount_blocked_no_cap](docs/screenshots/S06A_mount_blocked_no_cap.png)

- **S06B – mount still blocked with CAP_SYS_ADMIN (Seccomp wins)**  
  ![S06B_mount_blocked_with_cap](docs/screenshots/S06B_mount_blocked_with_cap.png)

---

### 7) Safety & portability checks
- **S07A – “must-have” syscalls present**  
  ![S07A_must_have_present](docs/screenshots/S07A_must_have_present.png)

- **S07B – Architectures mapped (AARCH64 + X86_64)**  
  ![S07B_architectures_list](docs/screenshots/S07B_architectures_list.png)

---

### 8) Prepublish checker
- **S08 – One-command prepublish pass**  
  ![S08_prepublish_pass](docs/screenshots/S08_prepublish_pass.png)

