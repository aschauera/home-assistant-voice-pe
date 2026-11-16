import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseAssemblyTests(unittest.TestCase):
    def test_assembles_exactly_one_standard_firmware_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources = root / "sources"
            build = root / "build" / "v1.4.4"
            output = root / "release"
            sources.mkdir()
            build.mkdir(parents=True)
            metadata = {
                "schema": 1,
                "tag": "v1.4.4",
                "commit": "a" * 40,
                "project_version": "1.4.4",
                "esphome_version": "2026.10.0",
                "entrypoint": "home-assistant-voice.factory.yaml",
                "source_archive": "home-assistant-voice-source-v1.4.4.tar.gz",
            }
            (sources / "firmware-release.json").write_text(json.dumps(metadata))
            (sources / "home-assistant-voice-source-v1.4.4.tar.gz").write_bytes(b"src")
            (sources / "home-assistant-voice.yaml").write_text("base\n")
            (sources / "home-assistant-voice.factory.yaml").write_text("factory\n")
            (sources / "SHA256SUMS.txt").write_text("stale\n")
            (build / "compiled.ota.bin").write_bytes(b"ota")
            (build / "compiled.factory.bin").write_bytes(b"factory")

            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts/assemble_firmware_release.py"),
                    "--tag",
                    "v1.4.4",
                    "--commit",
                    "a" * 40,
                    "--sources",
                    str(sources),
                    "--build",
                    str(root / "build"),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            assembled = json.loads((output / "firmware-release.json").read_text())
            self.assertEqual(2, assembled["schema"])
            self.assertEqual("standard-16mb", assembled["firmware"]["variant"])
            self.assertEqual(
                "home-assistant-voice-standard-v1.4.4.ota.bin",
                assembled["firmware"]["ota"]["path"],
            )
            checksum_names = {
                line.split("  ", 1)[1]
                for line in (output / "SHA256SUMS.txt").read_text().splitlines()
            }
            self.assertEqual(
                {path.name for path in output.iterdir() if path.name != "SHA256SUMS.txt"},
                checksum_names,
            )
            self.assertFalse((output / "home-assistant-voice.8mb.yaml").exists())

    def test_rejects_multiple_ota_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources = root / "sources"
            build = root / "build"
            sources.mkdir()
            build.mkdir()
            (sources / "firmware-release.json").write_text(
                json.dumps({"tag": "v1.4.4", "commit": "a" * 40})
            )
            (build / "one.ota.bin").write_bytes(b"one")
            (build / "two.ota.bin").write_bytes(b"two")
            (build / "one.factory.bin").write_bytes(b"factory")
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts/assemble_firmware_release.py"),
                    "--tag",
                    "v1.4.4",
                    "--commit",
                    "a" * 40,
                    "--sources",
                    str(sources),
                    "--build",
                    str(build),
                    "--output",
                    str(root / "output"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Expected exactly one *.ota.bin", result.stderr)


if __name__ == "__main__":
    unittest.main()
