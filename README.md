# Nanobot Voice PE firmware

This repository is a focused fork of the official ESPHome source code for the
[Home Assistant Voice: Preview Edition](https://www.home-assistant.io/voice-pe/).
The upstream project remains available at
[`esphome/home-assistant-voice-pe`](https://github.com/esphome/home-assistant-voice-pe).

> [!IMPORTANT]
> Das aktuelle gekoppelte Pre-Release ist Firmware [`v1.4.3`](https://github.com/aschauera/home-assistant-voice-pe/releases/tag/v1.4.3) zusammen mit HA Voice Bridge [`v1.4.3`](https://github.com/aschauera/NanoBotSkills/releases/tag/v1.4.3). Beide verwenden dieselbe SemVer und denselben `v`-Tag. Bis zur gemeinsamen Hardwarevalidierung bleiben beide Pre-Releases; historische Releases wie Firmware `0.2.1` und Bridge `v1.4.1` bleiben unverändert.

## Offener Dialogmodus

Die Custom Firmware unterstützt einen begrenzten halbduplexen Dialog über die
bestehende Home-Assistant-Assist-Pipeline. Ein Wake Word öffnet die Session;
nach jeder Antwort wartet das Gerät ohne neues Wake Word auf den nächsten Turn.
`Stop`, definierte Exit-Phrasen, Mute, die mittlere Taste, Fehler, zehn Minuten
Gesamtlaufzeit oder zwanzig Antworten beenden sie. Als exakte, nach STT
erkannte Exit-Phrasen gelten `Stop`, `Stopp`, `Tschüss`, `Tschüs`, `Ciao`,
`Bye`, `Goodbye`, `Auf Wiedersehen` und `Dialog beenden`. Nur `Stop` ist das
lokale Sleep-Word-Modell; alle STT-Phrasen sind Best Effort. Während auf eine
Frage gewartet wird, beenden fünf Sekunden ohne Sprachbeginn die Session. Der
Leerlauf-Timeout startet nach jeder Antwort neu und wird mit dem ersten
Sprachbeginn angehalten. Nur dieser Timeout spielt einmalig einen kurzen,
lokalen Bestätigungston vor dem orangefarbenen Abschlussimpuls ab. Manuelle
Exits und Fehler spielen diesen Ton nicht.

Der LED-Ablauf bleibt über Dialogzustände hinweg ruhig: ein kurzer grüner Ring
öffnet die Session; Warten und Zuhören teilen denselben violett atmenden Ring;
Verarbeitung und ein Remote-ACK bleiben langsam amberfarben; die Antwort nutzt
denselben Amber-Ton mit schnellerem Puls. Nach jeder Antwort wird wieder violett
gewartet. Ein normales Ende zeigt genau einen kurzen orangefarbenen Impuls,
Fehler blinken weiterhin rot. Der Diagnosesensor `Dialog state` behält die
genauen textuellen Zustände für Bridge-Diagnosen bei.

Eine eingebettete lokale Ansage „Einen Moment.“ kann über die ESPHome-Aktion
`dialog_remote_ack` ausgelöst werden. Die Conversation-Agent-Integration muss
diesen Hook erst nach erfolglosem Local-Intent-Routing aufrufen; die Firmware
selbst kann lokal und remote nicht unterscheiden.

Architektur, Zustandsübergänge, LED-Prioritäten, Integrationsvertrag, Grenzen
und Rollback sind in [`docs/dialogmodus.md`](docs/dialogmodus.md) dokumentiert.
Barge-in und Full-Duplex sind ausdrücklich nicht Bestandteil dieser Version.

Der Timeout-Ton und die Exit-Phrasen sind **nicht hardwarevalidiert**. Die
lokale Audioausgabe kann je nach Gerätelautstärke oder Audiopfad zu leise,
verzögert oder abgeschnitten sein. Risiken, Testvoraussetzungen und der
Rollback auf ein bekannt gutes Firmware-/Bridge-Paar stehen in
[`docs/ota-flashing.md`](docs/ota-flashing.md); diese Änderung erteilt keine
Flash-Freigabe.

## Nanobot LED override

The firmware exposes a **Nanobot LED state** select entity to Home Assistant.
Selecting a state temporarily overrides the stock Assist animation:

| Option | Visual feedback | Automatic reset |
|---|---|---|
| `off` | Return control to the stock firmware | immediate |
| `thinking` | slow amber breathing ring | 90 seconds |
| `ack` | same slow amber breathing ring; no separate blue indication | 1.5 seconds |
| `replying` | faster amber breathing ring | 90 seconds |
| `follow_up` | violet breathing ring | 90 seconds |
| `done` | green confirmation | 1 second |
| `error` | red flash | 3 seconds |

Startup failure, provisioning, loss of the Home Assistant connection, hardware
interaction, ringing timers, mute, and native Voice Assistant error/not-ready
states retain priority over the Nanobot override. Every long-lived override has
a 90-second fail-safe and boot always starts with the override disabled.

Home Assistant can drive the state with `select.select_option`, for example:

```yaml
action: select.select_option
target:
  entity_id: select.home_assistant_voice_0a6c07_nanobot_led_state
data:
  option: ack
```

The exact entity ID is assigned by Home Assistant and may differ.

## Bauen und installieren

GitHub kompiliert diese Firmware bewusst **nicht**. Pull Requests und Pushes auf
`dev` führen nur striktes YAML-Lint und die Contract-/Unit-Tests aus. Auch die
Release-Automation erzeugt keine Binaries: Sie hängt die drei versionierten
YAML-Dateien, ein vollständiges Source-Paket, Build-Metadaten und
SHA-256-Prüfsummen an das GitHub-Release.

Nanobot lädt ein unveränderliches Release lokal herunter, verifiziert Tag,
Commit und Prüfsummen und kompiliert es mit der im Release festgelegten
ESPHome-Version. Ohne `--flash` endet der Ablauf nach dem lokalen Build:

```bash
cd /home/nanobot/home-assistant-voice-pe
python3 scripts/deploy_firmware_release.py vX.Y.Z
```

Ein OTA-Flash ist ein eigener, ausdrücklich freizugebender Schritt. Das Script
verlangt dafür die Geräteadresse, ein vorhandenes bekannt gutes Rollback-Image
und die exakte Flash-Bestätigung. Das einzige produktive Kitchen Voice PE wird
niemals allein aufgrund eines Builds oder Releases geflasht.

Die vollständige Anleitung steht unter
[`docs/ota-flashing.md`](docs/ota-flashing.md). Die verbindliche Zuordnung von
Firmware- und Bridge-Releases steht unter
[`docs/release-pairing.md`](docs/release-pairing.md).

Für OTA wird ausschließlich das lokal erzeugte `.ota.bin` verwendet.
`.factory.bin` ist nur für USB-Installation oder Recovery bestimmt. Der
offizielle Webinstaller bleibt der letzte Recovery-Pfad:

https://esphome.github.io/home-assistant-voice-pe/

For upstream setup and troubleshooting, see
https://voice-pe.home-assistant.io/.
