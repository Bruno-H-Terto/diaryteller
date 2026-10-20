"""Translate the diary catalogues in `android/i18n` into Android resources.

One YAML file per language is the single source of truth for user-facing copy.
`extract` bootstraps a catalogue from legacy XML, `build` regenerates the
`res/values*` files and `check` fails when the generated files drift.

External effects: reads and writes files under `android/`. No network access.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOGUES = ROOT / "android" / "i18n"
RESOURCES = ROOT / "android" / "app" / "src" / "main" / "res"
BASE_LANGUAGE = "pt_br"
GENERATED = "GENERATED FILE - edit android/i18n/{name}.yml and run `make i18n`."
LANGUAGES_RESOURCE = "languages.xml"

EXTRA_ESCAPES = {"'": "\\'", '"': '\\"'}
ILLEGAL = set("<>&")


def catalogue_paths() -> list[Path]:
    """Return every catalogue, base language first."""
    paths = sorted(CATALOGUES.glob("*.yml"))
    return sorted(paths, key=lambda path: path.stem != BASE_LANGUAGE)


def load(path: Path) -> dict:
    """Read one catalogue; the file must expose `language`, `label` and `strings`."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not data.get("strings"):
        raise SystemExit(f"{path}: catalogue has no strings")
    return data


def escape(value: str) -> str:
    """Escape a catalogue value for an Android XML string resource."""
    escaped = []
    for char in value:
        if char in EXTRA_ESCAPES:
            escaped.append(EXTRA_ESCAPES[char])
        elif char in ILLEGAL:
            escaped.append(
                {"<": "&lt;", ">": "&gt;", "&": "&amp;"}[char],
            )
        else:
            escaped.append(char)
    return "".join(escaped)


def render(catalogue: dict, name: str) -> str:
    """Serialize one catalogue as an Android resource file."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!--",
        GENERATED.format(name=name),
        "-->",
        "<resources>",
    ]
    for key, value in catalogue["strings"].items():
        lines.append(f'    <string name="{key}">{escape(str(value))}</string>')
    for key, forms in (catalogue.get("plurals") or {}).items():
        lines.append(f'    <plurals name="{key}">')
        for quantity, value in forms.items():
            lines.append(f'        <item quantity="{quantity}">{escape(str(value))}</item>')
        lines.append("    </plurals>")
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def target_dir(catalogue: dict) -> Path:
    """Return the resource directory that holds one language."""
    normalized = catalogue["language"].lower().replace("-", "_")
    if normalized == BASE_LANGUAGE:
        return RESOURCES / "values"
    return RESOURCES / f"values-{catalogue['language']}"


def write(path: Path, content: str) -> bool:
    """Write `content` when it differs; returns whether the file changed."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def languages_xml(catalogues: list[dict]) -> str:
    """Build the language picker resource so a new catalogue is picked up automatically."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!--",
        "GENERATED FILE - edit android/i18n/*.yml and run `make i18n`.",
        "-->",
        "<resources>",
        '    <string-array name="app_languages">',
    ]
    for catalogue in catalogues:
        lines.append(f"        <item>{escape(catalogue['label'])}|{catalogue['language']}</item>")
    lines.extend(["    </string-array>", "</resources>"])
    return "\n".join(lines) + "\n"


def build(check_only: bool) -> int:
    """Generate every resource file; with `check_only` report drift instead of writing."""
    catalogues = [load(path) for path in catalogue_paths()]
    if not catalogues:
        raise SystemExit(f"no catalogue found in {CATALOGUES}")
    changed: list[str] = []
    for path, catalogue in zip(catalogue_paths(), catalogues):
        target = target_dir(catalogue) / "strings.xml"
        content = render(catalogue, path.stem)
        if check_only:
            matches = target.exists() and target.read_text(encoding="utf-8") == content
            if not matches:
                changed.append(str(target.relative_to(ROOT)))
        elif write(target, content):
            changed.append(str(target.relative_to(ROOT)))
    languages = RESOURCES / "values" / LANGUAGES_RESOURCE
    content = languages_xml(catalogues)
    if check_only:
        if not (languages.exists() and languages.read_text(encoding="utf-8") == content):
            changed.append(str(languages.relative_to(ROOT)))
    elif write(languages, content):
        changed.append(str(languages.relative_to(ROOT)))
    for name in changed:
        print(f"{'stale' if check_only else 'wrote'} {name}")
    if check_only:
        if changed:
            print("run `make i18n` to refresh the catalogues", file=sys.stderr)
        return 1 if changed else 0
    return 0


def extract() -> int:
    """Bootstrap `pt_br.yml` from the hand-written resource files, once."""
    strings: dict[str, str] = {}
    plurals: dict[str, dict[str, str]] = {}
    for path in sorted(RESOURCES.glob("values/*.xml")):
        if path.name in {"colors.xml", "themes.xml", LANGUAGES_RESOURCE}:
            continue
        root = ElementTree.parse(path).getroot()
        for node in root:
            if node.tag == "string":
                strings[node.attrib["name"]] = node.text or ""
            elif node.tag == "plurals":
                plurals[node.attrib["name"]] = {
                    item.attrib["quantity"]: item.text or "" for item in node
                }
    data = {
        "language": "pt-BR",
        "label": "Português (Brasil)",
        "strings": dict(sorted(strings.items())),
    }
    if plurals:
        data["plurals"] = dict(sorted(plurals.items()))
    path = CATALOGUES / f"{BASE_LANGUAGE}.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"wrote {path.relative_to(ROOT)} with {len(strings)} strings and {len(plurals)} plurals")
    return 0


def main() -> int:
    """Dispatch the catalog tool."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check", "extract"])
    arguments = parser.parse_args()
    if arguments.command == "extract":
        return extract()
    return build(check_only=arguments.command == "check")


if __name__ == "__main__":
    raise SystemExit(main())
