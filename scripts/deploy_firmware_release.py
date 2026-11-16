#!/usr/bin/env python3
"""Download, verify, and optionally flash a precompiled firmware release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
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


def read_checksum_manifest(downloads: Path) -> dict[str, str]:
    checksum_file = downloads / "SHA256SUMS.txt"
    if not checksum_file.is_file():
        raise SystemExit("Release does not contain SHA256SUMS.txt")
    checksums: dict[str, str] = {}
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        if (
            not separator
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or not name
            or "/" in name
            or "\\" in name
            or name in checksums
        ):
            raise SystemExit(f"Invalid checksum entry: {line!r}")
        checksums[name] = expected
    if not checksums:
        raise SystemExit("SHA256SUMS.txt is empty")
    return checksums


def verify_release_assets(downloads: Path) -> dict[str, str]:
    checksums = read_checksum_manifest(downloads)
    downloaded = {
        path.name
        for path in downloads.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    expected = set(checksums)
    if downloaded != expected:
        missing = sorted(expected - downloaded)
        unlisted = sorted(downloaded - expected)
        raise SystemExit(
            f"Release asset set differs from SHA256SUMS.txt; missing={missing}, unlisted={unlisted}"
        )
    for name, expected_digest in checksums.items():
        path = downloads / name
        actual = sha256(path)
        if actual != expected_digest:
            raise SystemExit(f"Checksum mismatch for {name}: {actual} != {expected_digest}")
        print(f"Checksum OK: {name}")
    return checksums


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
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(destination, filter="data")


def firmware_images(downloads: Path, metadata: dict[str, object]) -> tuple[Path, Path]:
    firmware = metadata.get("firmware")
    if not isinstance(firmware, dict):
        raise SystemExit(
            "This release has no precompiled firmware metadata. Use a newer release "
            "built by the release-only GitHub workflow."
        )
    if firmware.get("variant") != "standard-16mb":
        raise SystemExit(f"Unsupported firmware variant: {firmware.get('variant')!r}")

    images: list[Path] = []
    for kind in ("ota", "factory"):
        details = firmware.get(kind)
        if not isinstance(details, dict):
            raise SystemExit(f"Release metadata is missing firmware.{kind}")
        name = details.get("path")
        digest = details.get("sha256")
        if not isinstance(name, str) or Path(name).name != name:
            raise SystemExit(f"Invalid firmware.{kind}.path")
        image = downloads / name
        if not image.is_file() or sha256(image) != digest:
            raise SystemExit(f"Firmware metadata verification failed for {kind}")
        images.append(image)
    return images[0], images[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a precompiled Voice PE release; flashing is opt-in."
    )
    parser.add_argument("tag", help="Immutable release tag, for example v1.4.4")
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Working directory (default: ~/.cache/voice-pe-firmware/TAG)",
    )
    parser.add_argument(
        "--esphome",
        type=Path,
        help="ESPHome executable used only for flashing; defaults to the release-pinned venv",
    )
    parser.add_argument("--flash", action="store_true", help="Flash the verified OTA image")
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
    verified = work_dir / "verified"
    if downloads.exists():
        shutil.rmtree(downloads)
    downloads.mkdir(parents=True)

    run(
        [
            "gh",
            "release",
            "download",
            args.tag,
            "--repo",
            REPOSITORY,
            "--dir",
            str(downloads),
        ]
    )
    verify_release_assets(downloads)

    metadata = json.loads((downloads / "firmware-release.json").read_text(encoding="utf-8"))
    if metadata.get("schema") != 2 or metadata.get("tag") != args.tag:
        raise SystemExit("Release metadata schema or tag does not match the requested release")
    release_commit = resolve_release_commit(args.tag)
    if metadata.get("commit") != release_commit:
        raise SystemExit("Release metadata commit does not match the immutable Git tag")

    ota, factory = firmware_images(downloads, metadata)
    archive_name = metadata.get("source_archive")
    if not isinstance(archive_name, str) or Path(archive_name).name != archive_name:
        raise SystemExit("Invalid source_archive path in release metadata")
    archive = downloads / archive_name
    if not archive.is_file():
        raise SystemExit("Release source archive is missing")
    safe_extract(archive, source)
    entrypoint_name = str(metadata.get("entrypoint", ""))
    entrypoint = source / entrypoint_name
    if entrypoint_name != "home-assistant-voice.factory.yaml" or not entrypoint.is_file():
        raise SystemExit("Release source bundle does not contain the expected standard entrypoint")
    for name in ("home-assistant-voice.yaml", "home-assistant-voice.factory.yaml"):
        direct = downloads / name
        bundled = source / name
        if not direct.is_file() or direct.read_bytes() != bundled.read_bytes():
            raise SystemExit(f"Direct YAML asset differs from source bundle: {name}")

    verified.mkdir(parents=True, exist_ok=True)
    verified_ota = verified / ota.name
    verified_factory = verified / factory.name
    shutil.copy2(ota, verified_ota)
    shutil.copy2(factory, verified_factory)
    print(f"Verified OTA image: {verified_ota}")
    print(f"OTA SHA-256: {sha256(verified_ota)}")

    if not args.flash:
        print("Flash skipped. A separate explicit --flash invocation is required.")
        return
    if not args.device:
        raise SystemExit("--device is required with --flash")
    if args.flash_confirmation != FLASH_CONFIRMATION:
        raise SystemExit(f"--flash-confirmation must be exactly {FLASH_CONFIRMATION}")
    if not args.rollback_ota or not args.rollback_ota.resolve().is_file():
        raise SystemExit("--rollback-ota must point to a known-good existing OTA image")

    esphome_version = str(metadata["esphome_version"])
    esphome = (
        args.esphome
        or Path.home() / ".venvs" / f"esphome-{esphome_version}" / "bin/esphome"
    ).resolve()
    if not esphome.is_file():
        raise SystemExit(
            f"ESPHome {esphome_version} executable is missing: {esphome}. "
            "It is required for OTA upload, but not for release verification."
        )
    version_output = subprocess.run(
        [str(esphome), "version"], check=True, capture_output=True, text=True
    ).stdout
    if esphome_version not in version_output:
        raise SystemExit(
            f"ESPHome executable does not report required version {esphome_version}: "
            f"{version_output.strip()}"
        )

    rollback_copy = verified / f"rollback-{args.rollback_ota.name}"
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
            str(verified_ota),
            "--ota-platform",
            "esphome",
        ],
        cwd=source,
    )
    print("OTA upload completed. Verify the device and HA entities physically before acceptance.")


if __name__ == "__main__":
    main()
