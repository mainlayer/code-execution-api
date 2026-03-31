"""
Subprocess-based code execution sandbox with timeout enforcement.

Supported languages: python, javascript (node)

Security notes for production:
  - Run this service inside a container or VM with no network access.
  - Apply seccomp/AppArmor profiles to the worker process.
  - Use a resource-limited OS user for the subprocess.
  - Consider gVisor or Firecracker for stronger isolation.
"""

import subprocess
import sys
import tempfile
import os
from dataclasses import dataclass

DEFAULT_TIMEOUT = 10  # seconds
MAX_OUTPUT_BYTES = 64 * 1024  # 64 KB

LANGUAGE_CONFIG: dict[str, dict] = {
    "python": {
        "cmd": [sys.executable, "-u", "{file}"],
        "suffix": ".py",
    },
    "javascript": {
        "cmd": ["node", "{file}"],
        "suffix": ".js",
    },
}


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    language: str
    duration_ms: float


class SandboxError(Exception):
    pass


def execute_code(
    code: str,
    language: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> ExecutionResult:
    """
    Execute *code* in *language* inside a subprocess sandbox.

    Args:
        code:     Source code to run.
        language: 'python' or 'javascript'.
        timeout:  Maximum wall-clock seconds allowed.

    Returns:
        ExecutionResult with stdout, stderr, exit code, and timing.

    Raises:
        SandboxError: If the language is unsupported.
    """
    if language not in LANGUAGE_CONFIG:
        raise SandboxError(f"Unsupported language '{language}'. Supported: {list(LANGUAGE_CONFIG)}")

    config = LANGUAGE_CONFIG[language]

    import time

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=config["suffix"],
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        cmd = [part.replace("{file}", tmp_path) for part in config["cmd"]]

        start = time.monotonic()
        timed_out = False

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                text=True,
            )
            stdout = proc.stdout[:MAX_OUTPUT_BYTES]
            stderr = proc.stderr[:MAX_OUTPUT_BYTES]
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            stdout = ""
            stderr = f"Execution timed out after {timeout}s"
            exit_code = -1

        duration_ms = (time.monotonic() - start) * 1000

    finally:
        os.unlink(tmp_path)

    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        language=language,
        duration_ms=round(duration_ms, 2),
    )
