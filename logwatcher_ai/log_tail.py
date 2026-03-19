"""
Helpers for ingesting logs either from a plain file or directly from Docker.

Behavior:
- Reads logs from Docker using `docker logs -f <container>`
- Appends them to demo.log
- Parses JSON log lines into LogEvent objects
- Automatically deletes old log lines when demo.log reaches the max limit
"""

import asyncio
import json
import subprocess
from collections import deque
from pathlib import Path
from typing import Callable, Deque

from schemas import LogEvent


async def tail_file(
    path: str,
    on_event: Callable[[LogEvent], None],
    poll_interval: float = 0.25,
) -> None:
    """
    Follow a normal file like tail -f.

    Starts at the end of the file, so only NEW lines are processed.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)

        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(poll_interval)
                continue

            _parse_and_emit(line, on_event)


async def tail_docker_logs(
    container_name: str,
    output_path: str,
    on_event: Callable[[LogEvent], None],
    max_file_lines: int = 100_000,
    rewrite_every: int = 100,
    restart_delay: float = 2.0,
) -> None:
    """
    Follow Docker logs directly and mirror them into a local log file.

    Important:
    - Keeps ONLY the newest `max_file_lines` lines in demo.log
    - Deletes older lines automatically once the limit is exceeded
    - Reconnects if the Docker log stream stops
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)

    # Load existing file, but keep only the newest max_file_lines
    recent_lines: Deque[str] = deque(_read_last_lines(path, max_file_lines), maxlen=max_file_lines)

    # If file already has too many lines, trim it immediately on startup
    _rewrite_with_recent_lines(path, recent_lines)

    pending_since_rewrite = 0

    while True:
        print(f"[docker] connecting to container logs: {container_name}")

        process = None
        try:
            process = subprocess.Popen(
                ["docker", "logs", "-f", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            assert process.stdout is not None

            while True:
                line = await asyncio.to_thread(process.stdout.readline)

                if not line:
                    break

                line = line.rstrip("\r\n")
                if not line:
                    continue

                # Add newest line; deque(maxlen=...) automatically drops oldest line
                recent_lines.append(line)
                pending_since_rewrite += 1

                # Append immediately so demo.log keeps updating live
                with path.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(line + "\n")

                # Periodically rewrite the file so old lines are physically removed
                if pending_since_rewrite >= rewrite_every:
                    _rewrite_with_recent_lines(path, recent_lines)
                    pending_since_rewrite = 0

                _parse_and_emit(line, on_event)

            rc = process.wait()
            print(f"[docker] log stream ended, returncode={rc}")

        except FileNotFoundError:
            print("[docker] ERROR: docker CLI not found in PATH")
        except Exception as e:
            print(f"[docker] ERROR: {e}")
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()

        # Final trim before reconnecting
        if pending_since_rewrite > 0:
            _rewrite_with_recent_lines(path, recent_lines)
            pending_since_rewrite = 0

        print(f"[docker] reconnecting in {restart_delay}s...")
        await asyncio.sleep(restart_delay)


def _parse_and_emit(line: str, on_event: Callable[[LogEvent], None]) -> None:
    """
    Parse one JSON log line and emit a LogEvent.
    Ignore malformed lines.
    """
    line = line.strip()
    if not line:
        return

    try:
        obj = json.loads(line)
        event = LogEvent(**obj)
        on_event(event)
    except Exception:
        return


def _read_last_lines(path: Path, max_lines: int) -> list[str]:
    """
    Read only the newest max_lines from an existing file.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\r\n") for line in deque(f, maxlen=max_lines)]
    except FileNotFoundError:
        return []


def _rewrite_with_recent_lines(path: Path, recent_lines: Deque[str]) -> None:
    """
    Rewrite the file so it contains ONLY the newest lines.

    This is what physically deletes old logs from demo.log.
    """
    with path.open("w", encoding="utf-8", errors="replace") as f:
        for line in recent_lines:
            f.write(line + "\n")