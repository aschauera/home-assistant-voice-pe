#!/usr/bin/env python3
"""Download a source-only release, compile it locally, and optionally flash OTA."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

REPOSITORY = "aschauera/home-assistant-voice-pe"
FLASH_CONFIRMATION = "FLASH-KITCHEN-VOICE-PE"


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksums(downloads: Path) -> None:
    checksum_file = downloads / "SHA256SUMS.txt"
    if not checksum_file.is_file():
        raise SystemExit("Release does not contain SHA256SUMS.txt")
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        if not separator or "/" in name or "\\" in name:
            raise SystemExit(f"Invalid checksum entry: {line!r}")
        path = downloads / name
        if not path.is_file():
            raise SystemExit(f"Checksummed release asset is missing: {name}")
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"Checksum mismatch for {name}: {actual} != {expected}")
        print(f"Checksum OK: {name}")


def resolve_release_commit(tag: str) -> str:
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{REPOSITORY}/git/ref/tags/{tag}",
            "--jq",
            '.object.type + " " + .object.sha',
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    object_type, sha = result.split(" ", 1)
    if object_type == "tag":
        sha = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{REPOSITORY}/git/tags/{sha}",
                "--jq",
                ".object.sha",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    return sha


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(destination, filter="data")


def find_single_build_file(source: Path, filename: str) -> Path:
    matches = list((source / ".esphome/build").glob(f"*/.pioenvs/*/{filename}"))
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one {filename} after local compilation, found {len(matches)}"
        )
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile a released Voice PE YAML locally; flashing is opt-in."
    )
    parser.add_argument("tag", help="Immutable release tag, for example v1.4.3")
    parser.add_argument("--variant", choices=("standard", "8mb"), default="standard")
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Working directory (default: ~/.cache/voice-pe-firmware/TAG)",
    )
    parser.add_argument(
        "--esphome",
        type=Path,
        help="ESPHome executable; defaults to ~/.venvs/esphome-VERSION/bin/esphome",
    )
    parser.add_argument("--flash", action="store_true", help="Flash the locally built OTA image")
    parser.add_argument("--device", help="Voice PE host/IP; required with --flash")
    parser.add_argument(
        "--rollback-ota",
        type=Path,
        help="Known-good OTA image; required with --flash",
    )
    parser.add_argument(
        "--flash-confirmation",
        help=f"Required with --flash; exact value: {FLASH_CONFIRMATION}",
    )
    args = parser.parse_args()

    work_dir = (args.work_dir or Path.home() / ".cache/voice-pe-firmware" / args.tag).resolve()
    downloads = work_dir / "downloads"
    source = work_dir / "source"
    build_output = work_dir / "build"
    downloads.mkdir(parents=True, exist_ok=True)

    patterns = [
        "home-assistant-voice.yaml",
        "home-assistant-voice.factory.yaml",
        "home-assistant-voice.8mb.yaml",
        f"home-assistant-voice-source-{args.tag}.tar.gz",
        "firmware-release.json",
        "SHA256SUMS.txt",
    ]
    command = [
        "gh",
        "release",
        "download",
        args.tag,
        "--repo",
        REPOSITORY,
        "--dir",
        str(downloads),
        "--clobber",
    ]
    for pattern in patterns:
        command.extend(("--pattern", pattern))
    run(command)
    verify_checksums(downloads)

    metadata = json.loads((downloads / "firmware-release.json").read_text(encoding="utf-8"))
    if metadata.get("tag") != args.tag:
        raise SystemExit("Release metadata tag does not match requested tag")
    release_commit = resolve_release_commit(args.tag)
    if metadata.get("commit") != release_commit:
        raise SystemExit("Release metadata commit does not match the immutable Git tag")

    archive = downloads / str(metadata["source_archive"])
    if source.exists():
        shutil.rmtree(source)
    safe_extract(archive, source)
    for name in (
        "home-assistant-voice.yaml",
        "home-assistant-voice.factory.yaml",
        "home-assistant-voice.8mb.yaml",
    ):
        if (downloads / name).read_bytes() != (source / name).read_bytes():
            raise SystemExit(f"Direct YAML asset differs from source bundle: {name}")

    esphome_version = str(metadata["esphome_version"])
    esphome = (args.esphome or Path.home() / ".venvs" / f"esphome-{esphome_version}" / "bin/esphome").resolve()
    if not esphome.is_file():
        raise SystemExit(
            f"ESPHome {esphome_version} executable is missing: {esphome}. "
            "Install that exact version in an isolated local venv first."
        )
    version_output = subprocess.run(
        [str(esphome), "version"], check=True, capture_output=True, text=True
    ).stdout
    if esphome_version not in version_output:
        raise SystemExit(
            f"ESPHome executable does not report required version {esphome_version}: "
            f"{version_output.strip()}"
        )

    entrypoint = source / metadata["entrypoints"][args.variant]
    run([str(esphome), "compile", entrypoint.name], cwd=source)

    ota_source = find_single_build_file(source, "firmware.ota.bin")
    factory_source = find_single_build_file(source, "firmware.factory.bin")
    build_output.mkdir(parents=True, exist_ok=True)
    ota = build_output / f"home-assistant-voice-{args.variant}-{args.tag}.ota.bin"
    factory = build_output / f"home-assistant-voice-{args.variant}-{args.tag}.factory.bin"
    shutil.copy2(ota_source, ota)
    shutil.copy2(factory_source, factory)

    build_manifest = {
        "schema": 1,
        "tag": args.tag,
        "release_commit": release_commit,
        "variant": args.variant,
        "esphome_version": esphome_version,
        "entrypoint": entrypoint.name,
        "ota": {"path": ota.name, "sha256": sha256(ota)},
        "factory": {"path": factory.name, "sha256": sha256(factory)},
    }
    (build_output / "local-build.json").write_text(
        json.dumps(build_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Local build complete: {ota}")
    print(f"OTA SHA-256: {build_manifest['ota']['sha256']}")

    if not args.flash:
        print("Flash skipped. A separate explicit --flash invocation is required.")
        return
    if not args.device:
        raise SystemExit("--device is required with --flash")
    if args.flash_confirmation != FLASH_CONFIRMATION:
        raise SystemExit(f"--flash-confirmation must be exactly {FLASH_CONFIRMATION}")
    if not args.rollback_ota or not args.rollback_ota.resolve().is_file():
        raise SystemExit("--rollback-ota must point to a known-good existing OTA image")

    rollback_copy = build_output / f"rollback-{args.rollback_ota.name}"
    shutil.copy2(args.rollback_ota.resolve(), rollback_copy)
    print(f"Rollback image preserved at: {rollback_copy}")
    run(
        [
            str(esphome),
            "upload",
            entrypoint.name,
            "--device",
            args.device,
            "--file",
            str(ota),
            "--ota-platform",
            "esphome",
        ],
        cwd=source,
    )
    print("OTA upload completed. Verify the device and HA entities physically before acceptance.")


if __name__ == "__main__":
    main()
