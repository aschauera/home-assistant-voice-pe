from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = (ROOT / "home-assistant-voice.yaml").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
DOC = (ROOT / "docs/dialogmodus.md").read_text(encoding="utf-8")


class CustomFirmwareContractTest(unittest.TestCase):
    def test_esphome_version_is_pinned(self) -> None:
        self.assertIn("min_version: 2026.10.0", CONFIG)
        self.assertIn("esphome-version: 2026.10.0", WORKFLOW)

    def test_dialog_safety_contract(self) -> None:
        for expected in (
            "id: dialog_session_active",
            "id: dialog_session_timeout",
            "delay: 2min",
            "id(dialog_turn_count) >= 20",
            "voice_assistant.start_continuous:",
            "Ignoring wake word during active dialog (barge-in disabled)",
        ):
            self.assertIn(expected, CONFIG)

    def test_dialog_led_and_diagnostic_states_are_documented(self) -> None:
        for state in (
            "sleeping",
            "activating",
            "waiting",
            "listening",
            "processing",
            "remote_ack",
            "replying",
            "follow_up",
            "ending",
            "error",
        ):
            self.assertIn(state, DOC)

    def test_remote_ack_is_local_and_guarded(self) -> None:
        sound = ROOT / "sounds/remote_ack_einen_moment.mp3"
        self.assertTrue(sound.is_file())
        self.assertGreater(sound.stat().st_size, 1_000)
        self.assertIn("action: dialog_remote_ack", CONFIG)
        self.assertIn("id(dialog_session_active)", CONFIG)
        self.assertIn('sound_file: "remote_ack_einen_moment"', CONFIG)

    def test_vendored_cpp_matches_reviewed_upstream_commit(self) -> None:
        expected = {
            "voice_assistant.cpp": "b3506dcb44c7616c202e86ff2cd57cba31fb7aafd874414504a90827b1dd9535",
            "voice_assistant.h": "3712f58b5cb4bcd969026a722b13887273bec4bd24de1072b1f411ef5af4573a",
        }
        component = ROOT / "custom_components/voice_assistant"
        for name, digest in expected.items():
            actual = hashlib.sha256((component / name).read_bytes()).hexdigest()
            self.assertEqual(digest, actual, name)


if __name__ == "__main__":
    unittest.main()
