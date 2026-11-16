#!/usr/bin/env python3
"""Package the immutable ESPHome sources required for a local firmware build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DIRECT_ASSETS = (
    "home-assistant-voice.yaml",
    "home-assistant-voice.factory.yaml",
)
SOURCE_PATHS = DIRECT_ASSETS + (
    "custom_components",
    "sounds",
)
ESPHOME_VERSION_PATTERN = re.compile(r"^\s*min_version:\s*([^\s#]+)", re.MULTILINE)
PROJECT_VERSION_PATTERN = re.compile(r"^\s*version:\s*([^\s#]+)", re.MULTILINE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_versions() -> tuple[str, str]:
    base = (ROOT / "home-assistant-voice.yaml").read_text(encoding="utf-8")
    factory = (ROOT / "home-assistant-voice.factory.yaml").read_text(encoding="utf-8")
    esphome_match = ESPHOME_VERSION_PATTERN.search(base)
    project_match = PROJECT_VERSION_PATTERN.search(factory)
    if not esphome_match or not project_match:
        raise SystemExit("Could not determine ESPHome or project version from YAML")
    return esphome_match.group(1), project_match.group(1)


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for relative in SOURCE_PATHS:
        path = ROOT / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
        else:
            raise SystemExit(f"Required release source is missing: {relative}")
    return sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix())


def create_archive(output: Path, tag: str, files: list[Path]) -> Path:
    archive = output / f"home-assistant-voice-source-{tag}.tar.gz"
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for path in files:
            relative = path.relative_to(ROOT)
            tar.add(path, arcname=relative.as_posix(), recursive=False)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True, help="Release tag, for example v1.4.3")
    parser.add_argument("--commit", required=True, help="Full release commit SHA")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tag = args.tag.strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", tag):
        raise SystemExit(f"Invalid release tag: {tag}")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise SystemExit("--commit must be a full lowercase Git commit SHA")

    esphome_version, project_version = read_versions()
    if tag.removeprefix("v") != project_version:
        raise SystemExit(
            f"Tag {tag} does not match firmware project version {project_version}"
        )

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = iter_source_files()

    assets: list[Path] = []
    for name in DIRECT_ASSETS:
        destination = output / name
        destination.write_bytes((ROOT / name).read_bytes())
        assets.append(destination)

    archive = create_archive(output, tag, files)
    assets.append(archive)

    metadata = output / "firmware-release.json"
    metadata.write_text(
        json.dumps(
            {
                "schema": 1,
                "tag": tag,
                "commit": args.commit,
                "project_version": project_version,
                "esphome_version": esphome_version,
                "entrypoint": "home-assistant-voice.factory.yaml",
                "source_archive": archive.name,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assets.append(metadata)

    checksums = output / "SHA256SUMS.txt"
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(assets)),
        encoding="utf-8",
    )

    print(f"Packaged {len(files)} source files for {tag} in {output}")


if __name__ == "__main__":
    main()
