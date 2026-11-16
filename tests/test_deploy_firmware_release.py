import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "deploy_firmware_release", ROOT / "scripts" / "deploy_firmware_release.py"
)
DEPLOY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DEPLOY)


class ReleaseVerificationTests(unittest.TestCase):
    def create_release_assets(self, root: Path) -> tuple[Path, Path]:
        ota = root / "firmware.ota.bin"
        factory = root / "firmware.factory.bin"
        ota.write_bytes(b"ota")
        factory.write_bytes(b"factory")
        metadata = {
            "schema": 2,
            "tag": "v1.4.4",
            "firmware": {
                "variant": "standard-16mb",
                "ota": {"path": ota.name, "sha256": DEPLOY.sha256(ota)},
                "factory": {
                    "path": factory.name,
                    "sha256": DEPLOY.sha256(factory),
                },
            },
        }
        metadata_path = root / "firmware-release.json"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        checksums = {
            path.name: DEPLOY.sha256(path) for path in (ota, factory, metadata_path)
        }
        (root / "SHA256SUMS.txt").write_text(
            "".join(f"{digest}  {name}\n" for name, digest in sorted(checksums.items())),
            encoding="utf-8",
        )
        return ota, factory

    def test_verifies_complete_checksum_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.create_release_assets(root)
            checksums = DEPLOY.verify_release_assets(root)
            self.assertEqual(3, len(checksums))

    def test_rejects_tampered_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ota, _ = self.create_release_assets(root)
            ota.write_bytes(b"tampered")
            with self.assertRaisesRegex(SystemExit, "Checksum mismatch"):
                DEPLOY.verify_release_assets(root)

    def test_rejects_unlisted_release_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.create_release_assets(root)
            (root / "unexpected.bin").write_bytes(b"unexpected")
            with self.assertRaisesRegex(SystemExit, "unlisted=.*unexpected.bin"):
                DEPLOY.verify_release_assets(root)

    def test_selects_only_checksum_verified_standard_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ota, factory = self.create_release_assets(root)
            metadata = json.loads((root / "firmware-release.json").read_text())
            self.assertEqual((ota, factory), DEPLOY.firmware_images(root, metadata))
            metadata["firmware"]["variant"] = "8mb"
            with self.assertRaisesRegex(SystemExit, "Unsupported firmware variant"):
                DEPLOY.firmware_images(root, metadata)

    def test_legacy_source_only_release_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(SystemExit, "no precompiled firmware metadata"):
                DEPLOY.firmware_images(Path(temp), {"schema": 1})


if __name__ == "__main__":
    unittest.main()
