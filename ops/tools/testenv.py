"""Global test environment for the app and the backend.

`up` starts the pods, migrates and seeds the database, boots the emulator,
installs the debug app and opens the ports. `emulator` does only the device part,
`down` stops everything and `status` reports what is running.

External effects: runs docker compose, alembic, adb and gradle, all local.
"""

from __future__ import annotations

import argparse
import shutil
import sys

from ops.tools.devstack import (
    APK,
    APP_ID,
    COMPOSE,
    FORWARDED,
    REVERSED,
    ROOT,
    adb,
    compose_state,
    ensure_emulator,
    http_code,
    run,
    wait_postgres,
)


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


def summary() -> None:
    """Print the URLs and commands a developer needs next."""
    print("\nstack:\n" + compose_state())
    print("\nlogin: demo@example.com / password (dex)")
    print("app:   ports reversed 8001/8010/5556, bridge 5557")
    print("panel: make studio -> http://127.0.0.1:8099   checks: make check")


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
    adb("emu", "kill")
    print("stack and emulator stopped")


def status() -> None:
    """Report the environment without changing anything."""
    print("compose:\n" + compose_state())
    print("\ndevices:\n" + adb("devices"))
    print(f"bridge: {http_code(f'http://127.0.0.1:{FORWARDED}/health')}")
    print(f"studio: {http_code('http://127.0.0.1:8099/api/status')}")


def main() -> int:
    """Dispatch the environment commands."""
    parser = argparse.ArgumentParser(description="Global test environment")
    parser.add_argument("command", choices=["up", "down", "status", "emulator"])
    parser.add_argument("--no-app", action="store_true", help="skip building the app")
    arguments = parser.parse_args()
    if arguments.command == "up":
        up(install=not arguments.no_app)
    elif arguments.command == "emulator":
        ensure_emulator()
        install_app()
        summary()
    elif arguments.command == "down":
        down()
    else:
        status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
