"""Prepare a spoken conversation turn on the Android debug build.

With `--text`, Android TTS creates a local WAV. With `--audio`, the supplied
recording is copied into the app sandbox. In both cases the next microphone tap
in Conversations replays the file through the same offline recogniser.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

APP_ID = "com.callme.ai"
BRIDGE = "http://127.0.0.1:5557"


def post(path: str, payload: dict) -> dict:
    """Send one JSON request to the debug-only device bridge."""
    for attempt in range(3):
        request = urllib.request.Request(
            f"{BRIDGE}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if error.code != 422 or attempt == 2:
                detail = error.read().decode(errors="replace")
                raise SystemExit(f"bridge rejected {path}: {detail}") from error
            time.sleep(1)
    raise SystemExit(f"bridge did not answer {path}")


def copy_audio(source: Path) -> str:
    """Copy a test recording into the app-private directory via adb."""
    if not source.is_file():
        raise SystemExit(f"audio not found: {source}")
    target = f"simulation-{source.name}"
    subprocess.run(["adb", "push", str(source), f"/data/local/tmp/{target}"], check=True)
    subprocess.run(
        ["adb", "shell", "run-as", APP_ID, "cp", f"/data/local/tmp/{target}", f"files/{target}"],
        check=True,
    )
    return target


def main() -> None:
    """Create or copy the recording and arm replay mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--audio", type=Path)
    parser.add_argument("--language", default="pt-BR")
    args = parser.parse_args()
    if args.text:
        name = post("/voice/say", {"text": args.text, "language": args.language})["file"]
    else:
        name = copy_audio(args.audio)
    post("/voice/replay", {"path": name})
    print("simulação pronta: abra Conversas e toque no microfone")


if __name__ == "__main__":
    main()
