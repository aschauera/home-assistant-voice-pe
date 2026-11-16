#!/usr/bin/env python3
"""Combine packaged sources and one GitHub-built firmware variant for a release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_one(root: Path, pattern: str) -> Path:
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {pattern} in {root}, found {len(matches)}")
    return matches[0]


def copy_sources(source_dir: Path, output: Path) -> None:
    for source in sorted(source_dir.iterdir()):
        if source.is_file() and source.name != "SHA256SUMS.txt":
            shutil.copy2(source, output / source.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True, help="Release tag, for example v1.4.4")
    parser.add_argument("--commit", required=True, help="Full release commit SHA")
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", args.tag):
        raise SystemExit(f"Invalid release tag: {args.tag}")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise SystemExit("--commit must be a full lowercase Git commit SHA")

    sources = args.sources.resolve()
    build = args.build.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    copy_sources(sources, output)

    metadata_path = output / "firmware-release.json"
    if not metadata_path.is_file():
        raise SystemExit("Packaged sources do not contain firmware-release.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("tag") != args.tag or metadata.get("commit") != args.commit:
        raise SystemExit("Packaged source metadata does not match release tag and commit")

    ota_source = find_one(build, "*.ota.bin")
    factory_source = find_one(build, "*.factory.bin")
    basename = f"home-assistant-voice-standard-{args.tag}"
    ota = output / f"{basename}.ota.bin"
    factory = output / f"{basename}.factory.bin"
    shutil.copy2(ota_source, ota)
    shutil.copy2(factory_source, factory)

    metadata["schema"] = 2
    metadata.pop("entrypoints", None)
    metadata["entrypoint"] = "home-assistant-voice.factory.yaml"
    metadata["firmware"] = {
        "builder": "github-actions",
        "variant": "standard-16mb",
        "ota": {"path": ota.name, "sha256": sha256(ota)},
        "factory": {"path": factory.name, "sha256": sha256(factory)},
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assets = sorted(
        path for path in output.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in assets),
        encoding="utf-8",
    )
    print(f"Assembled {len(assets)} release assets for {args.tag}")


if __name__ == "__main__":
    main()
