"""Mechanics shared by the environment commands: compose, adb and waiting.

Kept apart from the CLI so each file stays small and readable. Everything here
touches only local resources: docker compose, the Android SDK and loopback.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_HOME = os.environ.get("ANDROID_HOME", str(Path.home() / "Android" / "Sdk"))
COMPOSE = ["docker", "compose", "-f", "ops/compose.yaml", "--env-file", ".env"]
AVD = os.environ.get("DIARY_AVD", "callme_api36")
APP_ID = "com.callme.ai"
APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
FORWARDED = "5557"
#: Ports the app and the browser reach from inside the device. 5556 is the OIDC
#: provider: without it the login screen opens and fails with connection refused.
REVERSED = ("8001", "8010", "5556")


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    """Run a command, raising with its output when it fails."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()[-5:]
        raise SystemExit(f"failed: {' '.join(command)}\n" + "\n".join(detail))
    return result


def adb(*arguments: str) -> str:
    """Call adb with the platform-tools binary from the SDK."""
    binary = str(Path(ANDROID_HOME) / "platform-tools" / "adb")
    return run([binary, *arguments]).stdout.strip()


def http_code(url: str) -> str:
    """Status code of one local endpoint; 000 means nothing answered."""
    return (
        subprocess.run(  # noqa: S603 - fixed command
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        or "000"
    )


def compose_state() -> str:
    """Return the compose services table."""
    return run([*COMPOSE, "ps", "--format", "{{.Name}} {{.State}}"]).stdout.strip()


def wait_postgres(timeout: int = 90) -> None:
    """Wait until the development database accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        probe = subprocess.run(  # noqa: S603 - fixed command
            ["docker", "exec", "diary-api-postgres-1", "pg_isready", "-U", "diary"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0:
            return
        time.sleep(2)
    raise SystemExit("postgres did not become ready in time")


def wait_device(timeout: int = 180) -> None:
    """Wait for the emulator to finish booting."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if adb("shell", "getprop", "sys.boot_completed").strip() == "1":
            return
        time.sleep(3)
    raise SystemExit("emulator did not boot in time")


def ensure_emulator() -> None:
    """Start the AVD when no device is attached.

    A 1080x2400 AVD needs more than the default guest memory, and a fresh image
    asks for an adb authorization the automation cannot accept, so both are
    passed explicitly.
    """
    if "device" in adb("devices"):
        return
    emulator = str(Path(ANDROID_HOME) / "emulator" / "emulator")
    if not Path(emulator).exists():
        raise SystemExit(f"emulator not found at {emulator}")
    window = [] if os.environ.get("DIARY_WINDOW") == "1" else ["-no-window"]
    flags = ["-no-audio", "-no-boot-anim", "-skip-adb-auth"]
    flags += ["-memory", os.environ.get("DIARY_AVD_MEMORY", "3072")]
    flags += ["-gpu", os.environ.get("DIARY_AVD_GPU", "swiftshader_indirect")]
    subprocess.Popen(  # noqa: S603 - fixed command
        [emulator, "-avd", AVD, *window, *flags],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    adb("wait-for-device")
    wait_device()
