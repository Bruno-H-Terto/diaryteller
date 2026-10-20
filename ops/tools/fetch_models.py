"""Fetch the on-device speech model the app bundles.

The model is not committed: it is a 31 MB binary that would bloat the repository
and it changes independently of the code. `make model` downloads it, verifies the
size and unpacks it into the Android assets, where the app picks it up on start.

External effects: network download and writes under `android/app/src/main/assets`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[2] / "android" / "app" / "src" / "main" / "assets"
MODELS = {
    "pt": (
        "vosk-model-small-pt-0.3",
        "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip",
    ),
}
EXPECTED_BYTES = 25_000_000


def installed(language: str) -> Path:
    """Asset directory for one language model."""
    return ASSETS / f"model-{language}"


def present(language: str) -> bool:
    """Whether the model files are already unpacked."""
    target = installed(language)
    return (target / "final.mdl").exists() and (target / "Gr.fst").exists()


def fetch(language: str) -> None:
    """Download and unpack one model into the assets directory."""
    name, url = MODELS[language]
    target = installed(language)
    with tempfile.TemporaryDirectory() as workspace:
        archive = Path(workspace) / "model.zip"
        print(f"downloading {url}")
        with urllib.request.urlopen(url) as response, archive.open("wb") as sink:
            shutil.copyfileobj(response, sink)
        size = archive.stat().st_size
        if size < EXPECTED_BYTES:
            raise SystemExit(f"download too small ({size} bytes); check the URL")
        if target.exists():
            shutil.rmtree(target)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(workspace)
        shutil.move(str(Path(workspace) / name), str(target))
    print(f"model {language} ready at {target}")


def main() -> int:
    """Report or install models."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", nargs="?", default="pt", choices=sorted(MODELS))
    parser.add_argument("--check", action="store_true", help="only report presence")
    arguments = parser.parse_args()
    if arguments.check:
        state = "present" if present(arguments.language) else "missing"
        print(f"model {arguments.language}: {state}")
        return 0 if state == "present" else 1
    if present(arguments.language):
        print(f"model {arguments.language} already unpacked")
        return 0
    fetch(arguments.language)
    return 0


if __name__ == "__main__":
    sys.exit(main())
