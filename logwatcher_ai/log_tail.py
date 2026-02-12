"""
Tail (follow) a log file like `tail -f`, but in Python.

- Reads new lines appended to the file
- Each line is expected to be JSON
- Parses JSON -> LogEvent
- Calls on_event(LogEvent) for each parsed event
"""

import asyncio
import json
from typing import Callable

from schemas import LogEvent


async def tail_file(
    path: str,
    on_event: Callable[[LogEvent], None],
    poll_interval: float = 0.25,
) -> None:
    """
    Continuously follow a file and call on_event(LogEvent) for each new JSON line.

    poll_interval controls how often we check for new content (seconds).
    """
    # Open in text mode; errors="replace" prevents crashes on weird characters
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        # Seek to end: only follow NEW logs (like tail -f)
        f.seek(0, 0)  # read from start of file

        while True:
            line = f.readline()

            # No new data yet
            if not line:
                await asyncio.sleep(poll_interval)
                continue

            line = line.strip()
            if not line:
                continue

            # Each line should be JSON (one object per line)
            try:
                obj = json.loads(line)
                event = LogEvent(**obj)
                on_event(event)
            except Exception:
                # For demos: ignore malformed lines
                # (Optionally you could store "parse_failed" events here)
                continue
