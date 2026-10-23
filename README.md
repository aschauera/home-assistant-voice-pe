# Nanobot Voice PE firmware

This repository is a focused fork of the official ESPHome source code for the
[Home Assistant Voice: Preview Edition](https://www.home-assistant.io/voice-pe/).
The upstream project remains available at
[`esphome/home-assistant-voice-pe`](https://github.com/esphome/home-assistant-voice-pe).

## Offener Dialogmodus

Die Custom Firmware unterstützt einen begrenzten halbduplexen Dialog über die
bestehende Home-Assistant-Assist-Pipeline. Ein Wake Word öffnet die Session;
nach jeder Antwort wartet das Gerät ohne neues Wake Word auf den nächsten Turn.
`Stop`, definierte Exit-Phrasen, Mute, die mittlere Taste, Fehler, zwei Minuten
Laufzeit oder zwanzig Turns beenden sie.

Die LED-Anzeige macht jede Phase sichtbar: Grün öffnet oder beendet die Session,
Violett wartet auf einen Folgeturn, die native blaue Animation hört zu, Amber
verarbeitet, ein kurzer blauer Puls bestätigt den Remote-Agenten, Cyan spricht
und Rot signalisiert einen Fehler. Der Diagnosesensor `Dialog state` zeigt den
Zustand zusätzlich in Home Assistant.

Eine eingebettete lokale Ansage „Einen Moment.“ kann über die ESPHome-Aktion
`dialog_remote_ack` ausgelöst werden. Die Conversation-Agent-Integration muss
diesen Hook erst nach erfolglosem Local-Intent-Routing aufrufen; die Firmware
selbst kann lokal und remote nicht unterscheiden.

Architektur, Zustandsübergänge, LED-Prioritäten, Integrationsvertrag, Grenzen
und Rollback sind in [`docs/dialogmodus.md`](docs/dialogmodus.md) dokumentiert.
Barge-in und Full-Duplex sind ausdrücklich nicht Bestandteil dieser Version.

## Nanobot LED override

The firmware exposes a **Nanobot LED state** select entity to Home Assistant.
Selecting a state temporarily overrides the stock Assist animation:

| Option | Visual feedback | Automatic reset |
|---|---|---|
| `off` | Return control to the stock firmware | immediate |
| `thinking` | amber clockwise spinner | 90 seconds |
| `ack` | blue pulse | 1.5 seconds |
| `replying` | cyan anticlockwise spinner | 90 seconds |
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

## Building and installing

The GitHub Actions **Build** workflow validates both firmware variants with
ESPHome 2026.10.0 and publishes build artifacts. The custom firmware intentionally disables the
official HTTP updater so an upstream release cannot silently overwrite it;
future updates are installed through ESPHome OTA or USB.

Do not flash an untested artifact onto the only production Voice PE. Download
the workflow artifact and use `home-assistant-voice-esp32s3.factory.bin` for the
initial USB installation. Keep the official web installer as the rollback path:

https://esphome.github.io/home-assistant-voice-pe/

For upstream setup and troubleshooting, see
https://voice-pe.home-assistant.io/.
