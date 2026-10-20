"""Bring up the global test environment: stack, database, device and app.

`up` is the single command a developer needs: it starts the pods, migrates and
seeds the database, boots the emulator, installs the debug app and opens the
ports the app and the studio panel use. `down` stops everything and `status`
reports what is running.

External effects: runs docker compose, alembic, adb and gradle. Never touches
production resources; every port and device is local.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
ANDROID_HOME = os.environ.get("ANDROID_HOME", str(Path.home() / "Android" / "Sdk"))
JAVA_HOME = os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")
COMPOSE = ["docker", "compose", "-f", "ops/compose.yaml", "--env-file", ".env"]
APP_ID = "com.callme.ai"
AVD = os.environ.get("DIARY_AVD", "callme_api36")
#: Ports the app and the browser reach from inside the device. 5556 is the OIDC
#: provider: without it the login screen opens and fails with connection refused.
REVERSED = ("8001", "8010", "5556")
FORWARDED = "5557"


def run(command: list[str], cwd: Path = ROOT, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command, raising with its output when it fails."""
    result = subprocess.run(command, cwd=cwd, capture_output=capture, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()[-5:]
        raise SystemExit(f"failed: {' '.join(command)}\n" + "\n".join(detail))
    return result


def adb(*arguments: str) -> str:
    """Call adb with the platform-tools binary from the SDK."""
    binary = str(Path(ANDROID_HOME) / "platform-tools" / "adb")
    return run([binary, *arguments]).stdout.strip()


def compose_state() -> str:
    """Return the compose services table."""
    return run([*COMPOSE, "ps", "--format", "{{.Name}} {{.State}}"]).stdout.strip()


def wait_postgres(timeout: int = 90) -> None:
    """Wait until the development database accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        probe = subprocess.run(
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
    """Start the configured AVD when no device is attached.

    A realistic 1080x2400 AVD needs more than the default guest memory, and a
    fresh image asks for an adb authorization that the automation cannot accept,
    so both are passed explicitly.
    """
    if "device" in adb("devices"):
        return
    emulator = str(Path(ANDROID_HOME) / "emulator" / "emulator")
    if not Path(emulator).exists():
        raise SystemExit(f"emulator not found at {emulator}")
    window = [] if os.environ.get("DIARY_WINDOW") == "1" else ["-no-window"]
    subprocess.Popen(
        [
            emulator,
            "-avd",
            AVD,
            *window,
            "-no-audio",
            "-no-boot-anim",
            "-skip-adb-auth",
            "-memory",
            os.environ.get("DIARY_AVD_MEMORY", "3072"),
            "-gpu",
            os.environ.get("DIARY_AVD_GPU", "swiftshader_indirect"),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    adb("wait-for-device")
    wait_device()


def build_app() -> None:
    """Compile the debug APK with gradle's incremental build."""
    run(["./gradlew", ":app:assembleDebug"], cwd=ROOT / "android")


def install_app() -> None:
    """Install the debug build and expose the ports it needs."""
    adb("install", "-r", str(APK))
    for port in REVERSED:
        adb("reverse", f"tcp:{port}", f"tcp:{port}")
    adb("forward", f"tcp:{FORWARDED}", f"tcp:{FORWARDED}")
    adb("shell", "am", "start", "-n", f"{APP_ID}/.MainActivity")


def up(install: bool) -> None:
    """Start the whole environment and print what is available."""
    if not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")
        print("created .env from .env.example")
    if not any((ROOT / "keys").glob("*")):
        run(["make", "keys"])
    run([*COMPOSE, "up", "-d", "--build"])
    wait_postgres()
    run(["poetry", "run", "alembic", "-c", "api/alembic.ini", "upgrade", "head"])
    run(["poetry", "run", "python", "-m", "identity.config.seed"])
    ensure_emulator()
    if install:
        build_app()
        install_app()
    summary()


def down() -> None:
    """Stop the stack and the emulator."""
    run([*COMPOSE, "down"])
    subprocess.run(
        [str(Path(ANDROID_HOME) / "platform-tools" / "adb"), "emu", "kill"],
        capture_output=True,
        check=False,
    )
    print("stack and emulator stopped")


def summary() -> None:
    """Print the URLs and commands a developer needs next."""
    print("\nstack:\n" + compose_state())
    print("\nlogin: demo@example.com / password (dex)")
    print("app:   emulator attached, ports reversed 8001/8010/5556, bridge 5557")
    print("panel: make studio   -> http://127.0.0.1:8099")
    print("checks: make check")


def status() -> None:
    """Report the environment without changing anything."""
    print("compose:\n" + compose_state())
    print("\ndevices:\n" + adb("devices"))
    for label, path in (("bridge", "/health"), ("studio", "/api/status")):
        port = FORWARDED if label == "bridge" else "8099"
        url = f"http://127.0.0.1:{port}{path}"
        code = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        print(f"{label}: {code}")


def main() -> int:
    """Dispatch the environment commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["up", "down", "status"])
    parser.add_argument("--no-app", action="store_true", help="skip building the app")
    arguments = parser.parse_args()
    if arguments.command == "up":
        up(install=not arguments.no_app)
    elif arguments.command == "down":
        down()
    else:
        status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
