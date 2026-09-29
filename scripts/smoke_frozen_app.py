"""Verify a frozen desktop app reaches and stays in its Qt event loop."""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--working-directory", type=Path)
    parser.add_argument("--startup-seconds", type=float, default=12)
    args = parser.parse_args()

    executable = args.executable.resolve()
    if not executable.is_file():
        parser.error(f"Executable hasil paket tidak ditemukan: {executable}")
    working_directory = (args.working_directory or executable.parent).resolve()
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    process = subprocess.Popen(
        [str(executable)],
        cwd=working_directory,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(args.startup_seconds)
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(f"Aplikasi keluar sebelum smoke check selesai (exit code {exit_code}).")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print(f"Frozen app startup OK: {executable.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
